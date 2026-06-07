from typing import Callable

from interpreter import Registers


def dbg_input(reg: Registers) -> Registers:
    reg._regs["stdin"] = input("Please enter input: ")
    return reg


def dbg_flusha(reg: Registers) -> Registers:
    print(repr(reg._regs["a"]))
    return reg


def dbg_dump(reg: Registers) -> Registers:
    print(f"{reg}")
    return reg


def dbg_wait(reg: Registers) -> Registers:
    input("Press any key to continue...")
    return reg


def dbg_flush(reg: Registers) -> Registers:
    print(str(reg._regs["stdout"]).replace("\\n", "\n"), end="")
    return reg


def dbg_flushnl(reg: Registers) -> Registers:
    message = str(reg._regs["stdout"]).replace("\\e", "\x1b")
    print(message)
    return reg


def dbg_str_to_float(reg: Registers) -> Registers:
    try:
        reg._regs["a"] = float(reg._regs["a"])
        return reg
    except ValueError:
        return reg


def dbg_float_to_str(reg: Registers) -> Registers:
    reg._regs["a"] = str(reg._regs["a"])
    return reg


def dbg_tostr(reg: Registers) -> Registers:
    reg._regs["stdout"] = str(reg._parameters[0])
    return reg


FUNCTIONS: dict[str, Callable] = {
    "flusha": dbg_flusha,
    "flush": dbg_flush,
    "flushnl": dbg_flushnl,
    "input": dbg_input,
    "dump": dbg_dump,
    "wait": dbg_wait,
    "stra": dbg_float_to_str,
    "floata": dbg_str_to_float,
    "tostr": dbg_tostr,
}
