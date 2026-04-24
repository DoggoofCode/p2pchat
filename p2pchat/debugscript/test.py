from runner import run

with open(__file__.replace("test.py", "test_scripts/main.dbg"), "r") as file:
    run(file.read())
