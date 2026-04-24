from dbg_stdlib import FUNCTIONS


class Token:
    text: str
    type: str  # l: literal, m: variable, o: operand, k: keyword
    subtype: str | None = None

    def __init__(self, type: str, text: str, subtype: str | None = None) -> None:
        self.text = text
        self.type = type
        if subtype:
            self.subtype = subtype
        elif not subtype and type == "o":
            self.subtype = (
                "keyword"
                if text
                not in ["stdout", "stdin", "r", "a", "b", "c", "d", "p1", "p2", "p3"]
                else "reg"
            )

    @property
    def t(self) -> str:
        return self.text

    def __repr__(self) -> str:
        return f"Token({self.type}, {repr(self.text)}, {self.subtype})"

    def real_val(
        self, variable_dictionary: dict[str, str | float], reg: dict[str, str | float]
    ) -> str | float:
        if self.type == "m":
            if (mem_loc := variable_dictionary.get(self.t[1:-1])) is not None:
                return mem_loc
        elif self.type == "o" and self.subtype == "reg":
            return reg[self.t]
        return self.t

    @classmethod
    def AutoType(cls, text: str):
        try:
            return Token("l", float(text), "float")  # pyright: ignore
        except ValueError:
            pass
        if is_mem(text):
            return Token("m", text)
        return Token("o", text)


def is_mem(n: str | Token) -> bool:
    if isinstance(n, str):
        return n[0] == "[" and n[-1] == "]"
    elif isinstance(n, Token):
        return n.type == "m"


def err(msg: str, line: int):
    print(f"Error@{line + 1}: {msg}")


def run(command: str):
    variable_dictionary: dict[str, str | float] = {"testvar": "goon"}
    dbg = False

    statement_token: list[str] = [i for i in command.replace(":", ";").split(";")]
    if statement_token[-1].isspace():
        statement_token = statement_token[:-1]

    token_array: list[list[Token]] = []
    for index, command in enumerate(statement_token):
        char_pointer: int = 0
        token: str = ""
        # Add new array for instruction
        token_array.append([])

        # Tokenizer
        while char_pointer < len(command):
            # We KNOW the next one must be a operator
            if len(token_array[-1]) > 0 and token_array[-1][-1].t in ["sig", "label"]:
                while char_pointer < len(command) and command[char_pointer] != " ":
                    token += command[char_pointer]
                    char_pointer += 1
                if token_array[-1][-1].t == "sig":
                    token_array[-1].append(Token("o", token, "signal"))
                elif token_array[-1][-1].t == "label":
                    token_array[-1].append(Token("o", token, "label_name"))
                token = ""
            elif command[char_pointer] in ["\n", "\t"]:
                pass
            elif command[char_pointer] == "$":
                char_pointer = len(command)
                continue
            elif command[char_pointer] == '"' and not token:
                char_pointer += 1
                while command[char_pointer] != '"':
                    token += command[char_pointer]
                    char_pointer += 1
                token_array[-1].append(Token("l", token, "str"))
                token = ""
            elif command[char_pointer] == "[" and not token:
                while command[char_pointer] != "]":
                    token += command[char_pointer]
                    char_pointer += 1
                token_array[-1].append(Token("m", token + "]"))
                token = ""
            elif command[char_pointer] == " ":
                if token:
                    token_array[-1].append(Token.AutoType(token))
                    token = ""
            else:
                token += command[char_pointer]
            char_pointer += 1
        if token:
            token_array[-1].append(Token.AutoType(token))

    token_array = [t for t in token_array if t]

    # Set up regs
    reg: dict[str, str | float] = {
        # Used for stdin and stdout
        "stdout": "",
        "stdin": "",
        # The result of previous comparison
        "r": 0,
        # General Purpose Regs
        "a": "",
        "b": "",
        "c": "",
        "d": "",
        # Parameters
        "p1": "",
        "p2": "",
        "p3": "",
    }
    labels: dict[str, tuple[int, int]] = {}
    call_back = []

    if dbg:
        for i, tok_grp in enumerate(token_array):
            print(f"{i}: {tok_grp}")
    # Identify Labels
    for index, tk in enumerate(token_array):
        if tk[0].t == "label":
            return_count = 0
            inspected_token = index + 1
            while (
                not (token_array[inspected_token][0].t == "ret" and return_count == 0)
                and inspected_token < len(token_array) - 2
            ):
                if token_array[inspected_token][0].t == "label":
                    return_count += 1
                if token_array[inspected_token][0].t == "ret":
                    return_count -= 1
                inspected_token += 1
            labels[tk[1].t] = (index + 1, inspected_token)

    if dbg:
        print(labels)
    # Find start
    if labels.get("main"):
        line_num = labels["main"][0] - 1
    else:
        err("No main label", 0)
        return

    while line_num + 1 < len(token_array):
        line_num += 1
        if not (t_op_buffer := token_array[line_num]):
            continue
        op_buffer = [o.t for o in t_op_buffer]

        if dbg:
            print(
                f"Line:{line_num} Operation: {op_buffer}: \x1b[2m\n\tRegs: {reg}\n\tVariables: {variable_dictionary}\n\tCallback: {call_back[:10]}\x1b[0m"
            )

        match op_buffer[0]:
            case "set":
                # set dest source
                if op_buffer[1] in list(reg.keys()):
                    if is_mem(t_op_buffer[2]):
                        if (
                            var_val := variable_dictionary.get(op_buffer[2][1:-1])
                        ) is not None:
                            reg[op_buffer[1]] = var_val
                        elif t_op_buffer[2].subtype == "reg":
                            reg[op_buffer[1]] = reg[op_buffer[2]]
                        else:
                            err(
                                f"Variable '{op_buffer[2][1:-1]}' does not exist",
                                line_num,
                            )
                            return
                    else:
                        reg[op_buffer[1]] = (
                            reg[op_buffer[2]]
                            if t_op_buffer[2].subtype == "reg"
                            else op_buffer[2]
                        )
                elif is_mem(t_op_buffer[1]):
                    if is_mem(t_op_buffer[2]):
                        if (
                            var_val := variable_dictionary.get(op_buffer[2][1:-1])
                        ) is not None:
                            variable_dictionary[op_buffer[1][1:-1]] = var_val
                        elif t_op_buffer[2].subtype == "reg":
                            variable_dictionary[op_buffer[1][1:-1]] = reg[op_buffer[2]]
                        else:
                            err(
                                f"Variable '{op_buffer[2][1:-1]}' does not exist",
                                line_num,
                            )
                            return
                    else:
                        variable_dictionary[op_buffer[1][1:-1]] = (
                            reg[op_buffer[2]]
                            if t_op_buffer[2].subtype == "reg"
                            else op_buffer[2]
                        )
                else:
                    err(f"cannot set '{op_buffer[1]}' to '{op_buffer[2]}'", line_num)
                    return
            case "sig":
                match op_buffer[1]:
                    case "flush":
                        print(reg["stdout"])
                    case "exit":
                        print(
                            f"{'\x1b[31m' if int(reg['a']) != 0 else ''}Exit code: {reg['a']}\x1b[0m"
                        )
                        return None
                    case "wait":
                        input("Press any key to continue...")
                        continue
                    case "toFloat":
                        try:
                            reg["a"] = float(reg["a"])
                        except ValueError:
                            reg["r"] = 0
                    case "toStr":
                        try:
                            reg["a"] = str(reg["a"])
                        except ValueError:
                            reg["r"] = 0
                    case _:
                        found = False
                        for name, func in FUNCTIONS.items():
                            if op_buffer[1] == name:
                                found = True
                                func(reg)
                        if not found:
                            err(
                                f"Signal {op_buffer[1]} not found, trying checking linked libraries",
                                line_num,
                            )
            # Jumping
            case "label":
                if new_line_num := labels.get(op_buffer[1]):
                    line_num = new_line_num[1]
                    continue
                else:
                    err(f"No identier {op_buffer[1]}", line_num)
                    return
            case "goto":
                if new_line_num := labels.get(op_buffer[1]):
                    call_back.append(line_num)
                    line_num = new_line_num[0] - 1
                    continue
                else:
                    err(f"No identier {op_buffer[1]}", line_num)
                    return
            case "ret":
                if len(call_back) < 1:
                    err(
                        "No location to call back to (call_back array is empty)",
                        line_num,
                    )
                    return
                line_num = call_back.pop()
                continue
            # Conditions
            case "eq":
                value1 = t_op_buffer[1].real_val(variable_dictionary, reg)
                value2 = t_op_buffer[2].real_val(variable_dictionary, reg)
                if isinstance(value1, int):
                    value1 = float(value1)
                if isinstance(value2, int):
                    value2 = float(value2)
                if value1 == value2:
                    reg["r"] = 1
                else:
                    reg["r"] = 0
            case "gt" | "lt":
                value1 = t_op_buffer[1].real_val(variable_dictionary, reg)
                value2 = t_op_buffer[2].real_val(variable_dictionary, reg)
                if isinstance(value1, int):
                    value1 = float(value1)
                if isinstance(value2, int):
                    value2 = float(value2)
                if isinstance(value1, type(value2)):
                    if op_buffer[0] == "gt":
                        reg["r"] = 1 if value1 > value2 else 0  # pyright: ignore[reportOperatorIssue]
                    else:
                        reg["r"] = 1 if value1 < value2 else 0  # pyright: ignore[reportOperatorIssue]
            case "cjmp":
                if reg["r"] == 1:
                    if new_line_num := labels.get(op_buffer[1]):
                        call_back.append(line_num)
                        line_num = new_line_num[0] - 1
                        continue
                    else:
                        err(f"No identier {op_buffer[1]}", line_num)
                        return
            # Math
            case "add" | "sub":
                val2: float
                if op_buffer[2] in list(reg.keys()):
                    if not isinstance(temp := reg[op_buffer[2]], float):
                        err(
                            f"Cannot add non-float reg:{op_buffer[2]} \x1b[2mValue: {reg[op_buffer[2]]}\x1b[0m",
                            line_num,
                        )
                        return
                    else:
                        val2 = temp
                elif is_mem(t_op_buffer[2]):
                    val2 = float(t_op_buffer[2].real_val(variable_dictionary, reg))
                else:
                    # Cannot save to literal
                    if t_op_buffer[2].subtype != "float":
                        err(f"Cannot add non float {op_buffer[2]}", line_num)
                    val2 = float(t_op_buffer[2].t)

                if op_buffer[0] == "sub":
                    val2 = -val2

                if op_buffer[1] in list(reg.keys()):
                    reg_val = reg[op_buffer[1]]
                    if isinstance(reg_val, float):
                        reg[op_buffer[1]] = reg_val + val2
                    else:
                        err(
                            f"Cannot add non-float reg:{op_buffer[1]} \x1b[2mValue: {reg[op_buffer[1]]}\x1b[0m",
                            line_num,
                        )
                        return
                elif is_mem(t_op_buffer[1]):
                    variable_dictionary[op_buffer[1][1:-1]] = (
                        float(t_op_buffer[1].real_val(variable_dictionary, reg)) + val2
                    )
                else:
                    # Cannot save to literal
                    err(
                        f"Cannot add {op_buffer[2]} to literal {op_buffer[1]}", line_num
                    )
                    return
            case "mul" | "div":
                if op_buffer[2] in list(reg.keys()):
                    if not isinstance(temp := reg[op_buffer[2]], float):
                        err(
                            f"Cannot add non-float reg:{op_buffer[2]} \x1b[2mValue: {reg[op_buffer[2]]}\x1b[0m",
                            line_num,
                        )
                        return
                    else:
                        val2 = temp
                elif is_mem(t_op_buffer[2]):
                    val2 = float(t_op_buffer[2].real_val(variable_dictionary, reg))
                else:
                    # Cannot save to literal
                    if t_op_buffer[2].subtype != "float":
                        err(f"Cannot add non float {op_buffer[2]}", line_num)
                    val2 = float(t_op_buffer[2].t)

                if op_buffer[0] == "div":
                    val2 = 1 / val2

                if op_buffer[1] in list(reg.keys()):
                    reg_val = reg[op_buffer[1]]
                    if isinstance(reg_val, float):
                        reg[op_buffer[1]] = reg_val * val2
                    else:
                        err(
                            f"Cannot add non-float reg:{op_buffer[1]} \x1b[2mValue: {reg[op_buffer[1]]}\x1b[0m",
                            line_num,
                        )
                        return
                elif is_mem(t_op_buffer[1]):
                    variable_dictionary[op_buffer[1][1:-1]] = (
                        float(t_op_buffer[1].real_val(variable_dictionary, reg)) * val2
                    )
                else:
                    # Cannot save to literal
                    err(
                        f"Cannot add {op_buffer[2]} to literal {op_buffer[1]}", line_num
                    )
                    return
            case _:
                print(
                    f"[DEBUG SCRIPT] Operator '\x1b[1m{op_buffer[0]}\x1b[0m' not recognized \x1b[2m(args: {' '.join(op_buffer[1:])})\x1b[0m"
                )

    print("\x1b[1mIncomplete termination\x1b[0m")
