import json as js
import os


class GrpFiles:
    def __init__(self, filepath: str) -> None:
        self.user_table: dict[str, list[str]] = {}
        # TODO: Define dicts for all others later
        for entry in os.scandir(filepath):
            if entry.is_file():
                if entry.name == "user_table.json":
                    with open(entry.path, "w") as file:
                        self._user_table = js.loads(file.read())
                if entry.name == "message_dht.json":
                    pass
