import typing


def dbg_input(reg: dict[str, str | float]) -> dict[str, str | float]:
    reg["stdin"] = input("Please enter input: ")
    return reg


def dbg_flusha(reg: dict[str, str | float]) -> dict[str, str | float]:
    print(repr(reg["a"]))
    return reg


def dbg_dump(reg: dict[str, str | float]) -> dict[str, str | float]:
    print(f"{reg}")
    return reg


def dbg_to_float(reg: dict[str, str | float]) -> dict[str, str | float]:
    # p1 holds the name of the register to floatize
    location = reg["p1"]
    if location not in ["stdout", "stdin", "r", "a", "b", "c", "d", "p1", "p2", "p3"]:
        reg["r"] = -1
        return reg
    try:
        reg[location] = float(reg[location])
    except ValueError:
        reg["r"] = -1
    return reg


def dbg_to_str(reg: dict[str, str | float]) -> dict[str, str | float]:
    # p1 holds the name of the register to floatize
    location = reg["p1"]
    if location not in ["stdout", "stdin", "r", "a", "b", "c", "d", "p1", "p2", "p3"]:
        reg["r"] = -1
        return reg
    try:
        reg[location] = str(reg[location])
    except ValueError:
        reg["r"] = -1
    return reg


def dbg_wait(reg: dict[str, str | float]) -> dict[str, str | float]:
    input("Press any key to continue...")
    return reg


def dbg_flush(reg: dict[str, str | float]) -> dict[str, str | float]:
    print(str(reg["stdout"]).replace("\\n", "\n"), end="")
    return reg


def dbg_flushnl(reg: dict[str, str | float]) -> dict[str, str | float]:
    print(f"{reg['stdout']}\n", end="")
    return reg


MACROS: dict[str, str] = {
    "if": "cjmp _; label _",
}

FUNCTIONS: dict[str, typing.Callable] = {
    "flusha": dbg_flusha,
    "flush": dbg_flush,
    "flushnl": dbg_flushnl,
    "input": dbg_input,
    "dump": dbg_dump,
    "mk_flt": dbg_to_float,
    "mk_str": dbg_to_str,
    "wait": dbg_wait,
}
