import json as js
import os


class GrpFiles:
    def __init__(self, filepath: str) -> None:
        self.group_fp = filepath
        self.user_table: dict[str, list[str]] = {}
        # TODO: Define dicts for all others later
        for entry in os.scandir(filepath):
            if entry.is_file():
                if entry.name == "user_table.json":
                    with open(entry.path, "r") as file:
                        self._user_table = js.load(file)
                if entry.name == "message_dht.json":
                    pass

    def push_user_table(self) -> None:
        with open(os.path.join(self.group_fp, "user_table.json"), "w") as outpath:
            js.dump(self.user_table, outpath, indent=4)
