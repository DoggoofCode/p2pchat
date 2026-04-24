from runner import run

with open(__file__.replace("test.py", "test_scripts/greaterof2.dbg"), "r") as file:
    run(file.read())
