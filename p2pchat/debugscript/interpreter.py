import argparse
import os
import re
import sys
from typing import Callable, Literal, Self, Union, overload

DataType = Union[str, float]
WHITESPACE = ["\n", "\t", " "]
ENDOFSTATEMENT = [":", ";"]
INLINE_MATH = ["+", "-", "*", "/"]
COMMENT = "%"
PAIRS = {
    '"': '"',
    "[": "]",
    "(": ")",
}
OPERATORS = {
    "set": (2, 2),
    "sig": (1, 2),
    "jmp": (1, 1),
    "label": (1, 1),
    "ret": (0, 0),
    "pop": (0, 0),
    "push": (0, 0),
    "gt": (2, 2),
    "lt": (2, 2),
    "eq": (2, 2),
    "cjmp": (1, 1),
    "hjmp": (0, 0),
    "chjmp": (0, 0),
    "add": (2, 2),
    "sub": (2, 2),
    "div": (2, 2),
    "mul": (2, 2),
}
REGISTERS = [
    "a",
    "b",
    "c",
    "stdin",
    "stdout",
    "result",
    "accumulator",
    "p1",
    "p2",
    "p3",
]
ITALIC = "\x1b[3m"
UNITALIC = "\x1b[23m"
ALLOWED_MATH: dict[str, list[tuple[type, ...]]] = {
    "+": [(float, float), (str, str), (float,)],
    "-": [(float, float), (str, str), (float,)],
    "*": [(float, float), (float, str)],
    "/": [(float, float)],
}
COMMUNICATIVE_OPS: list[str] = ["+", "*"]


class MathExpr:
    def __init__(self, values: list[DataType], operation: str) -> None:
        self.values = values
        self.operation = operation

    @property
    def res(self) -> DataType | None:
        if ALLOWED_MATH.get(self.operation) is None:
            return None
        sig = ALLOWED_MATH.get(self.operation, [])
        arg_types = tuple(type(arg) for arg in self.values)
        if not (
            arg_types in sig
            or (self.operation in COMMUNICATIVE_OPS and arg_types[::-1] in sig)
        ):
            return None
        try:
            match self.operation:
                case "+":
                    # Aka, unary
                    if len(self.values) == 1:
                        return self.values[0]
                    elif len(self.values) == 2:
                        return self.values[0] + self.values[1]  # pyright:ignore
                case "-":
                    # Aka, unary
                    if len(self.values) == 1:
                        return self.values[0]
                    elif len(self.values) == 2:
                        return self.values[0] - self.values[1]  # pyright:ignore
                case "*":
                    return self.values[0] * self.values[1]  # pyright:ignore
                case "/":
                    return self.values[0] / self.values[1]  # pyright:ignore
                case "_":
                    raise NotImplementedError(
                        f"Operation {self.operation} not implemented!"
                    )

        except Exception as e:
            raise Exception(e)


class Token:
    text: DataType
    """
    l: literal (text, float),
    m: variable (both buffer and register)
    i: identifier (signal name, label name, etc.)
    k: keyword (operator)
    p: parameter (for signal or function (to come))
    """
    type: str
    subtype: str | None = None

    def __init__(self, type: str, text: str, subtype: str | None = None) -> None:
        self.text = text
        self.type = type
        self.subtype = subtype

    def __repr__(self) -> str:
        single_char = ""
        if isinstance(self.text, str) and len(self.text) == 1:
            single_char = f"\x1b[3m({hex(ord(self.text[0]))})\x1b[23m"

        return f"Token({self.type}: '\x1b[4m{self.text}\x1b[24m'{single_char}, \x1b[2m{self.subtype}\x1b[22m)"

    @classmethod
    def AutoLiteral(cls, lit: str):
        sub: str
        try:
            lit = float(lit)  # pyright:ignore
            sub = "float"
        except ValueError:
            if lit.startswith("(") and lit.endswith(")"):
                sub = "expr"
            else:
                sub = "str"
        return cls("l", lit, sub)

    @property
    def st(self) -> str:
        return str(self.text)


def mem_addr(x: str) -> bool:
    if x:
        return x[-1] == "]" and x[0] == "["
    else:
        return False


class Identifier(str):
    @property
    def debuffered(self):
        if not self:
            return self
        if self[0] == "[" and self[-1] == "]":
            return Identifier(self[1:-1])
        else:
            return self

    @classmethod
    def clean(cls, value: str) -> Self:
        if len(value) < 1:
            raise Exception("Cannot make empty string and identifier")
        if value[0] == "[" and value[-1] == "]":
            return cls(value[1:-1])
        else:
            return cls(value)


class Registers:
    _regs: dict[str, DataType] = {
        "stdin": "",
        "stdout": "",
        "a": "",
        "b": "",
        "c": "",
        "result": 0,
        "accumulator": 0,
    }
    _parameters: list[DataType] = []

    def __init__(self) -> None:
        self._regs = {
            "stdin": "",
            "stdout": "",
            "a": "",
            "b": "",
            "c": "",
            "result": 0,
            "accumulator": 0,
        }

    def set(self, name: str, value: DataType) -> None:
        if name[0] == "p":
            raise NotImplementedError("Parameter setting not implemented")
        if self._regs.get(name) is not None:
            self._regs[name] = value

    def get(self, name: str) -> DataType | None:
        if name[0] == "p":
            raise NotImplementedError("Parameter setting not implemented")
        if self._regs.get(name) is not None:
            return self._regs[name]
        else:
            return None

    def __repr__(self) -> str:
        return f"Regs({self._regs}, p: {self._parameters})"


class VariableScope:
    def __init__(self) -> None:
        self.variables: dict[Identifier, DataType] = {}

    def add(self, name: Identifier, value: DataType) -> None:
        self.variables[name] = value

    def get(self, name: Identifier) -> DataType | None:
        return self.variables.get(name)

    def is_var(self, var_name: Identifier) -> DataType:
        if (res := self.variables.get(var_name.debuffered)) is None:
            raise Exception(f"No variable {var_name}")
        return res

    def __repr__(self) -> str:
        return f"VarScope({self.variables})"


class LabelNode:
    name: str
    start: int
    end: int
    children: list[Self] = []

    def __init__(self, name: str, start: int, end: int) -> None:
        self.name = name
        self.start = start
        self.end = end
        self.children = []

    def search(self, name: str) -> int | None:
        # Returns the index of the main label
        for i, c in enumerate(self.children):
            if c.name == name:
                return i
        if name == self.name:
            return -1
        return None

    def int(self, index: int) -> int | None:
        for i, child in enumerate(self.children):
            if index <= child.end and index >= child.start:
                return i
        return None

    def new_child(self, child: Self) -> None:
        self.children.append(child)

    def __repr__(self) -> str:
        return f"Node({self.name}, {self.children}: {len(self.children)})"


class Interpreter:
    def __init__(self, *, debug: bool = False) -> None:

        self.debug = debug

        self.raw_script: str
        self.real_ln: list[int] = []
        self.base_node = LabelNode("HEAD", 0, 0)
        self.all_label_node = LabelNode("HEAD", 0, 0)
        self.callback_stack: list[tuple[int, bool]] = [(-1, True)]
        self.token_array: list[list[Token]] = []
        self.regs: Registers = Registers()
        self.reg_stack: list[Registers] = []
        self.variable_scope: VariableScope = VariableScope()
        self.variable_stack: list[VariableScope] = []
        self.sig_functions: dict[str, Callable] = {}
        self.runtime_sum: int = 0

    def err(self, line: int, message: str) -> None:
        print(f"\x1b[31mFatal Error @ Line {self.real_ln[line]}: {message}")
        exit(1)

    def complete_interpreter_notes(self) -> None:
        # Adding Multifiles
        # #link for python files(signals, etc.), #add for dbg files (tbd)
        all_start_interpreter_flags: list[str] = re.findall("#.*\n", self.raw_script)
        for int_flag in all_start_interpreter_flags:
            split_flag: list[str] = int_flag[1:-1].split(" ")
            replacement: str = ""
            match split_flag[0]:
                case "add":
                    pass
                case "link":
                    file_path = f"{'/'.join(__file__.split('/')[:-1])}/{split_flag[1]}"
                    if not file_path.endswith(".py"):
                        file_path += ".py"
                    # Add the directory of the target file to sys.path
                    module_dir = os.path.dirname(file_path)
                    module_name = os.path.splitext(os.path.basename(file_path))[0]

                    sys.path.insert(0, module_dir)

                    # Import the module normally
                    module = __import__(module_name)
                    sig_funcs: dict[str, Callable] = module.FUNCTIONS
                    for key, value in sig_funcs.items():
                        self.sig_functions[key] = value

            self.raw_script = self.raw_script.replace(int_flag[:-1], replacement)

    def tokenize(self) -> None:
        character_pointer: int = 0
        token_text: str = ""
        lexed_script: list[list[str]] = [[]]

        # PASS 1: Generates strings
        while character_pointer < len(self.raw_script):
            character = self.raw_script[character_pointer]
            if character in WHITESPACE:
                if token_text:
                    lexed_script[-1].append(token_text)
                    token_text = ""
            elif character in ENDOFSTATEMENT:
                if token_text:
                    lexed_script[-1].append(token_text)
                    token_text = ""
                lexed_script.append([])
                self.real_ln.append(
                    self.raw_script[0:character_pointer].count("\n") + 1
                )
            elif character == COMMENT:
                while self.raw_script[character_pointer] != "\n":
                    character_pointer += 1
            elif character in list(PAIRS.keys()):
                if token_text:
                    lexed_script[-1].append(token_text)
                    token_text = ""
                end_char: str = PAIRS[character]
                token_text += character
                character_pointer += 1
                while self.raw_script[character_pointer] != end_char:
                    token_text += self.raw_script[character_pointer]
                    character_pointer += 1
                lexed_script[-1].append(token_text + end_char)
                if lexed_script[-1][-1][0] == '"':
                    lexed_script[-1][-1] = lexed_script[-1][-1][1:-1]
                token_text = ""
            else:
                token_text += character
            # Moved to next character BY DEFAULT
            character_pointer += 1

        lexed_script = [cmd for cmd in lexed_script if cmd]

        if self.debug:
            print(
                "\x1b[1mLexer Output:\x1b[0m\n"
                + "\n".join(
                    [
                        f"{self.real_ln[i]}: {lexed_units}"
                        for i, lexed_units in enumerate(lexed_script)
                    ]
                )
            )

        # PASS 2 Generate Tokens
        for index, command in enumerate(lexed_script):
            self.token_array.append([])
            operator = command[0]

            self.token_array[-1].append(Token("k", command[0], None))

            # Checks the the number of operands and within the upper and lower limits
            if OPERATORS.get(operator) is None:
                self.err(
                    index,
                    f"Operator \x1b[3m'{operator}'\x1b[23m not found",
                )
                return
            if not (
                len(command) - 1 >= OPERATORS[operator][0]
                and len(command) - 1 <= OPERATORS[operator][1]
            ):
                self.err(
                    index,
                    f"Incorrect number of arguments provided to '\x1b[3m{operator}\x1b[23m'",
                )
            match operator:
                case "set":
                    # Destination
                    if command[1] in REGISTERS:
                        self.token_array[-1].append(Token("m", command[1], "reg"))
                    elif mem_addr(command[1]):
                        self.token_array[-1].append(Token("m", command[1], "addr"))
                    else:
                        self.err(
                            index,
                            f"Cannot set a value to literal '\x1b[3m{command[1]}\x1b[23m'",
                        )

                    # Source
                    if command[2] in REGISTERS:
                        self.token_array[-1].append(Token("m", command[2], "reg"))
                    elif mem_addr(command[2]):
                        self.token_array[-1].append(Token("m", command[2], "addr"))
                    else:
                        self.token_array[-1].append(Token.AutoLiteral(command[2]))
                case "label" | "jmp" | "cjmp":
                    self.token_array[-1].append(Token("i", command[1], "label"))
                case "sig":
                    # add the first op as a signal
                    self.token_array[-1].append(Token("i", command[1], "signal"))
                    # a parameter exists!
                    if len(command) > 2:
                        self.token_array[-1].append(Token("p", command[2]))
                case "add" | "sub" | "mul" | "div":
                    # Destination
                    if command[1] in REGISTERS:
                        self.token_array[-1].append(Token("m", command[1], "reg"))
                    elif mem_addr(command[1]):
                        self.token_array[-1].append(Token("m", command[1], "addr"))
                    else:
                        self.err(
                            index,
                            f"Cannot set a value to literal '\x1b[3m{command[1]}\x1b[23m'",
                        )

                    # Source
                    if command[2] in REGISTERS:
                        self.token_array[-1].append(Token("m", command[2], "reg"))
                    elif mem_addr(command[2]):
                        self.token_array[-1].append(Token("m", command[2], "addr"))
                    else:
                        self.token_array[-1].append(Token.AutoLiteral(command[2]))
                        # if self.token_array[-1][-1].subtype != "float":
                        #     self.err(
                        #         index,
                        #         f"Tried to add with non-float literal '\x1b[3m{command[2]}\x1b[23m'",
                        #     )
                case "gt" | "lt" | "eq":
                    # Value 1
                    if command[1] in REGISTERS:
                        self.token_array[-1].append(Token("m", command[1], "reg"))
                    elif mem_addr(command[1]):
                        self.token_array[-1].append(Token("m", command[1], "addr"))
                    else:
                        self.token_array[-1].append(Token.AutoLiteral(command[2]))
                        if self.token_array[-1][-1].subtype != "float":
                            self.err(
                                index,
                                f"Tried to compare with non-float literal '\x1b[3m{command[2]}\x1b[23m'",
                            )

                    # Value 2
                    if command[2] in REGISTERS:
                        self.token_array[-1].append(Token("m", command[2], "reg"))
                    elif mem_addr(command[2]):
                        self.token_array[-1].append(Token("m", command[2], "addr"))
                    else:
                        self.token_array[-1].append(Token.AutoLiteral(command[2]))
                        if self.token_array[-1][-1].subtype != "float":
                            self.err(
                                index,
                                f"Tried to compare with non-float literal '\x1b[3m{command[2]}\x1b[23m'",
                            )
                case "ret" | "push" | "pop" | "cjmp" | "chjmp":
                    pass
                case _:
                    self.err(
                        index, f"Operator not recognized: '\x1b[3m{operator}\x1b[23m'"
                    )

        # PASS 3 Resolve Anonymous Labels
        anonymous_counter: int = 0
        for index, instruction in enumerate(self.token_array):
            for op_idx, op in enumerate(instruction):
                if op.subtype == "label" and op.st[0] == "_" and len(op.st) < 2:
                    if (
                        instruction[op_idx - 1].text == "cjmp"
                        or instruction[op_idx - 1].text == "jmp"
                    ):
                        self.token_array[index][
                            op_idx
                        ].text = f"_anon{anonymous_counter}"
                    if instruction[op_idx - 1].st == "label":
                        self.token_array[index][
                            op_idx
                        ].text = f"_anon{anonymous_counter}"
                        anonymous_counter += 1

        if self.debug:
            print(
                "\x1b[1mToken Array:\x1b[0m\n"
                + "\n".join(
                    [
                        f"{self.real_ln[i]}: {lexed_units}"
                        for i, lexed_units in enumerate(self.token_array)
                    ]
                )
            )

    def print_label_tree(self, node: LabelNode, depth: int = 0) -> None:
        print(
            f"{depth * '  '}\x1b[1m{node.name}\x1b[0m {self.real_ln[node.start]}/{self.real_ln[node.end]}:"
        )
        for c in node.children:
            self.print_label_tree(c, depth + 1)

    def label_search(self, command_line: int) -> LabelNode:
        target_label = self.all_label_node
        node_idx: int | None = target_label.int(command_line)
        while node_idx is not None:
            target_label = target_label.children[node_idx]
            node_idx = target_label.int(command_line)
        return target_label

    def resolver(self) -> None:
        # Resolve labels
        start_stack: list[tuple[str, int]] = []  # TokenArray with label
        label_groups: list[tuple[str, int, int]] = []
        command_index: int = 0
        while command_index < len(self.token_array):
            if self.token_array[command_index][0].text == "label":
                start_stack.append(
                    (str(self.token_array[command_index][1].text), command_index)
                )
            elif self.token_array[command_index][0].text == "ret":
                corresponding_start = start_stack.pop()
                label_groups.append((*corresponding_start, command_index))
            command_index += 1

        label_groups = list(reversed(label_groups))

        if self.debug:
            print(
                "\x1b[1mLabel List\x1b[0m\n"
                + "\n".join(
                    [
                        f"Name: \x1b[4m{i[0]}\x1b[0m @ ({i[1]},{i[2]})"
                        for i in label_groups
                    ]
                )
            )

        for index, label_grp in enumerate(label_groups):
            # walking in the list to find the parenthood of the interval
            parent_stack: list[str] = []
            for grp in label_groups[:index]:
                if grp[1] < label_grp[1]:
                    # Meaning it is close thus its parent
                    parent_stack.append(grp[0])

            if not parent_stack:
                if label_grp[0][0] != "_":
                    self.base_node.new_child(LabelNode(*label_grp))
                self.all_label_node.new_child(LabelNode(*label_grp))
            else:
                target_node: LabelNode = self.base_node
                all_target_node: LabelNode = self.all_label_node
                while parent_stack:
                    popped_parent = parent_stack.pop(0)
                    if popped_parent[0] != "_":
                        new_target = target_node.search(popped_parent)
                    else:
                        new_target = -1
                    new_all_target = all_target_node.search(popped_parent)
                    if new_target is None or new_all_target is None:
                        self.err(
                            0,
                            "Labels in parent stack not found when walking to said parent node",
                        )
                        return
                    else:
                        if new_target > 0:
                            target_node = target_node.children[new_target]
                        all_target_node = all_target_node.children[new_target]
                if label_grp[0][0] != "_":
                    target_node.new_child(LabelNode(*label_grp))
                all_target_node.new_child(LabelNode(*label_grp))

        if self.debug:
            print("\x1b[1mNo-Anon Label Tree\x1b[0m")
            self.print_label_tree(self.base_node)
            print("\x1b[1mAll Label Tree\x1b[0m")
            self.print_label_tree(self.all_label_node)

    # Takes in a parentesized math block (..)
    def inline_math(self, expr: str) -> DataType | None:
        # Implement bodmas
        expr = expr[1:-1]
        char_ptr = 0
        tokens: list[DataType] = []
        token = ""
        while char_ptr < len(expr):
            char = expr[char_ptr]
            if char == '"':
                enclosed = char
                while char_ptr < len(expr) and expr[char_ptr] != '"':
                    enclosed += expr[char_ptr]
                res = self.inline_math(enclosed + '"')
                if not res:
                    return None
                tokens.append(res)
            if char == "(":
                enclosed = char
                while char_ptr < len(expr) and expr[char_ptr] != ")":
                    enclosed += expr[char_ptr]
                res = self.inline_math(enclosed + ")")
                if not res:
                    return None
                tokens.append(res)
            elif char in INLINE_MATH:
                if token:
                    tokens.append(token)
                    token = ""
                tokens.append(char)
            else:
                token += char
            char_ptr += 1
        if token:
            tokens.append(token)

        # Resolve all non-floats
        for index, tok in enumerate(tokens):
            if tok in INLINE_MATH:
                continue
            if tok in REGISTERS:
                real_tok = Token("m", tok, "reg")
            elif isinstance(tok, str) and mem_addr(tok):
                real_tok = Token("m", tok, "addr")
            else:
                real_tok = Token.AutoLiteral(str(tok))

            if not (val := self.getval(real_tok, allow_literal=True)):
                return None
            tokens[index] = val

        mth_expr = MathExpr([tokens[0], tokens[2]], str(tokens[1]))

        return mth_expr.res

    @overload
    def getval(
        self, t: Token, *, force_float: Literal[True], allow_literal: bool = False
    ) -> float | None: ...

    @overload
    def getval(
        self,
        t: Token,
        *,
        force_float: Literal[False] = False,
        allow_literal: bool = False,
    ) -> DataType | None: ...

    def getval(
        self, t: Token, *, force_float: bool = False, allow_literal=False
    ) -> DataType | None:
        value: DataType | None
        if t.type == "l" and allow_literal:
            if t.subtype == "expr":
                value = self.inline_math(t.st)
            else:
                value = t.text
        elif t.type == "m":
            if t.subtype == "reg":
                value = self.regs.get(t.st)
            elif t.subtype == "addr":
                source_ident = Identifier.clean(t.st)
                value = self.variable_scope.get(source_ident)
            else:
                return None
        else:
            return None
        if not isinstance(value, float) and force_float:
            return None
        return value

    def setval(self, t: Token, value: DataType) -> None:
        if t.subtype == "reg":
            self.regs.set(t.st, value)
        elif t.subtype == "addr":
            destination_ident = Identifier.clean(t.st)
            self.variable_scope.add(destination_ident, value)

    def walk_tree(self) -> None:
        main_label: int | None = self.base_node.search("main")
        if main_label is None:
            self.err(0, "No main label found. Please ensure a main label exists")
            return
        row_ptr: int = self.base_node.children[main_label].start + 1

        while row_ptr < len(self.token_array):
            self.runtime_sum += 1
            operation: list[Token] = self.token_array[row_ptr]
            operand: Token = operation[0]
            params: list[Token] = operation[1:]
            value: DataType | None = ""
            value2: DataType | None = ""
            if self.debug:
                print(f"Command {row_ptr}: {ITALIC}{operation}{UNITALIC}")

            match operand.text:
                case "label":
                    row_ptr = self.label_search(row_ptr).end
                case "set":
                    value = self.getval(params[1], allow_literal=True)

                    if value is None:
                        self.err(
                            row_ptr,
                            f"Value at {ITALIC}'{params[1]}'{UNITALIC} does not exist",
                        )
                        return

                    self.setval(params[0], value)
                case "add" | "sub" | "mul" | "div":
                    # Gets value of first number for operation
                    value = self.getval(params[1], allow_literal=True)

                    # Errors out if wrong type
                    if value is None:
                        self.err(
                            row_ptr,
                            (
                                f"The value contained in {ITALIC}'{params[1].st}'{UNITALIC} was empty or a non-float, "
                                f"therefore {ITALIC}'{operand.text}'{UNITALIC} is not permitted"
                            ),
                        )
                        return

                    # Get second value of the operation
                    value2 = self.getval(params[0])

                    if value2 is None:
                        self.err(
                            row_ptr,
                            (
                                f"The value contained in {ITALIC}'{params[0].st}'{UNITALIC} was empty or a non-float, "
                                f"therefore {ITALIC}'{operand.text}'{UNITALIC} is not permitted"
                            ),
                        )
                        return

                    result: MathExpr
                    if operand.text == "add":
                        result = MathExpr([value2, value], "+")
                    elif operand.text == "sub":
                        result = MathExpr([value2, value], "-")
                    elif operand.text == "mul":
                        result = MathExpr([value2, value], "*")
                    elif operand.text == "div":
                        result = MathExpr([value2, value], "/")
                    else:
                        self.err(row_ptr, f"Unrecognized operand {operand.text}")
                        return

                    # Check for errors
                    if result.res is None:
                        self.err(
                            row_ptr,
                            (
                                f"The operation {ITALIC}'{operand.text}'{UNITALIC} is not permitted on the values {value} and {value2}"
                            ),
                        )
                        return

                    self.setval(params[0], result.res)
                case "gt" | "lt" | "eq":
                    value = self.getval(params[0], allow_literal=True, force_float=True)

                    if value is None:
                        self.err(
                            row_ptr,
                            f"Value at {ITALIC}'{params[0]}'{UNITALIC} does not exist",
                        )
                        return

                    value2 = self.getval(
                        params[1], allow_literal=True, force_float=True
                    )

                    if value2 is None:
                        self.err(
                            row_ptr,
                            f"Value at {ITALIC}'{params[1]}'{UNITALIC} does not exist",
                        )
                        return

                    binary_operator: bool

                    match operand.text:
                        case "eq":
                            binary_operator = value == value2
                        case "lt":
                            binary_operator = value < value2
                        case "gt":
                            binary_operator = value > value2

                    if binary_operator:
                        self.setval(Token("m", "result", "reg"), 1)
                    else:
                        self.setval(Token("m", "result", "reg"), 0)
                case "jmp" | "cjmp":
                    if operand.text == "cjmp" and not bool(self.regs._regs["result"]):
                        row_ptr += 1
                        continue

                    parent_node: LabelNode = self.base_node
                    grandparent_node: LabelNode = self.base_node
                    next_node_index: int | None = parent_node.int(row_ptr)

                    all_node_parent: LabelNode = self.all_label_node
                    all_node_grandparent: LabelNode = self.all_label_node
                    next_all_node_index: int | None = all_node_parent.int(row_ptr)
                    while (
                        next_node_index is not None or next_all_node_index is not None
                    ):
                        if next_node_index is not None:
                            grandparent_node = parent_node
                            parent_node = parent_node.children[next_node_index]
                            next_node_index = parent_node.int(row_ptr)

                        if next_all_node_index is not None:
                            all_node_grandparent = all_node_parent
                            all_node_parent = all_node_parent.children[
                                next_all_node_index
                            ]
                            next_all_node_index = all_node_parent.int(row_ptr)

                    grandparental: bool = True
                    if params[0].st[0] == "_":
                        valid_jmp = all_node_grandparent.search(params[0].st)
                        if valid_jmp is None:
                            valid_jmp = all_node_parent.search(params[0].st)
                            grandparental = False
                    else:
                        valid_jmp = grandparent_node.search(params[0].st)
                        if valid_jmp is None:
                            valid_jmp = parent_node.search(params[0].st)
                            grandparental = False
                    if valid_jmp is None:
                        self.err(
                            row_ptr,
                            f"Cannot jump to {ITALIC}'{params[0]}'{UNITALIC} from {self.real_ln[row_ptr]}",
                        )
                        return

                    self.callback_stack.append((row_ptr, params[0].st[0] != "_"))
                    if params[0].st[0] != "_":
                        self.variable_stack.append(self.variable_scope)
                        self.variable_scope = VariableScope()

                    if params[0].st[0] == "_":
                        used_node = (
                            all_node_grandparent if grandparental else all_node_parent
                        )
                        if valid_jmp < 0:
                            row_ptr = used_node.start
                        else:
                            row_ptr = used_node.children[valid_jmp].start
                    else:
                        used_node = grandparent_node if grandparental else parent_node
                        if valid_jmp < 0:
                            row_ptr = used_node.start
                        else:
                            row_ptr = used_node.children[valid_jmp].start
                case "hjmp" | "chjmp":
                    if operand.text == "chjmp" and not bool(self.regs._regs["result"]):
                        row_ptr += 1
                        continue
                    # Pejorative Range
                    parent_node = self.all_label_node
                    next_node_index = parent_node.int(row_ptr)

                    while next_node_index is not None:
                        parent_node = parent_node.children[next_node_index]
                        next_node_index = parent_node.int(row_ptr)
                    # Start of the current label
                    row_ptr = parent_node.start

                case "ret":
                    if len(self.callback_stack) > 0:
                        new_row_ptr, grandparental = self.callback_stack.pop()
                        if new_row_ptr < 0:
                            # We have reached the end of the program, one can exit
                            row_ptr = len(self.token_array)
                        else:
                            row_ptr = new_row_ptr
                            if grandparental:
                                self.variable_scope = self.variable_stack.pop()
                    else:
                        self.err(
                            row_ptr,
                            f"Trying to return from no label, {ITALIC}(Callstack is empty){UNITALIC}",
                        )
                case "push":
                    self.reg_stack.append(self.regs)
                    self.regs = Registers()
                case "pop":
                    if len(self.reg_stack) < 1:
                        self.err(row_ptr, "Cannot pop register class of an empty stack")
                        return
                    self.regs = self.reg_stack.pop()
                case "sig":
                    if params[0].st[:3] == "int":
                        match params[0].st[4:]:
                            case "var":
                                print(self.variable_scope, self.variable_stack)
                    else:
                        if self.sig_functions.get(params[0].st) is None:
                            self.err(
                                row_ptr,
                                f"Signal {ITALIC}{params[0].st}{UNITALIC} not found, ensure that it is #link-ed",
                            )
                            return
                        if params[-1].type == "p":
                            param_toks = []
                            for val in params[-1].st[1:-1].split(","):
                                if val in REGISTERS:
                                    param_toks.append(Token("m", val, "reg"))
                                elif mem_addr(val):
                                    param_toks.append(Token("m", val, "addr"))
                                else:
                                    param_toks.append(Token.AutoLiteral(val))
                                v = self.getval(param_toks[-1], allow_literal=True)
                                if not v:
                                    self.err(
                                        row_ptr,
                                        f"Could not resolve token {ITALIC}{param_toks[-1]}{UNITALIC} within the parameter {ITALIC}{params[-1]}{UNITALIC}",
                                    )
                                    return
                                self.regs._parameters.append(v)
                        self.sig_functions[params[0].st](self.regs)
                        self.regs._parameters = []
                case _:
                    self.err(
                        row_ptr,
                        f"Unrecognized operand: \x1b[3m{self.token_array[row_ptr][0]}\x1b[0m",
                    )
                    return
            row_ptr += 1

    def run(self, script: str) -> None:
        self.raw_script = script
        if self.debug:
            print(f"{ITALIC}Resolving interpreter notes...{UNITALIC}")
        self.complete_interpreter_notes()
        if self.debug:
            print(f"{ITALIC}Interpreter notes resolved!{UNITALIC}")
            print(f"{ITALIC}Tokenizing...{UNITALIC}")
        self.tokenize()
        if self.debug:
            print(f"{ITALIC}Tokenization complete!{UNITALIC}")

            print(f"{ITALIC}Resolving all entries...{UNITALIC}")
        self.resolver()
        if self.debug:
            print(f"{ITALIC}All labels resolved...{UNITALIC}")
            print(f"{ITALIC}Running Program...{UNITALIC}")
        self.walk_tree()  # Not really a tree but who cares
        if self.debug:
            print(f"{ITALIC}Program complete!{UNITALIC}")
            print(
                f"\x1b[1m\n Runtime Eff. Ratio: {ITALIC}{self.runtime_sum / len(self.token_array):.3g}{UNITALIC}\x1b[0m "
            )


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="ScriptLang Parser",
        description="Interprets .sl, .slo, and .dbg files written in the ScriptLang language",
    )
    parser.add_argument("filename")
    parser.add_argument("-d", "--debug", action="store_true")
    args = parser.parse_args()
    file: str = args.filename
    if not os.path.exists(file):
        print(f"\x1b[31m Fatal Error: Path {file} does not exist\x1b[0m")
        return
    with open(file, "r") as f:
        script = f.read()
    if not script.replace(" ", "").replace("\n", "").replace("\t", ""):
        print(f"\x1b[31m Fatal Error: {file} is empty, or contains no code\x1b[0m")
        return

    int = Interpreter(debug=args.debug)
    int.run(script)


if __name__ == "__main__":
    main()
