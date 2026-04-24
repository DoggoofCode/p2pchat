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


FUNCTIONS: dict[str, typing.Callable] = {
    "flusha": dbg_flusha,
    "input": dbg_input,
    "dump": dbg_dump,
    "mk_flt": dbg_to_float,
}
