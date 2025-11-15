import base64
import os
import shutil

class Responder:
    MESSAGE_GROUPS: dict[bytes, str] = {}

    def __getitem__(self, name: bytes, /) -> str:
        return self.MESSAGE_GROUPS[name]

    def _filevalid_base64_encoded(self, name: bytes) -> str:
        return base64.b64encode(name).decode("utf-8").replace("/", "_")

    def _filevalid_base64_decode(self, name: str) -> bytes:
        return base64.b64decode(name.replace("_", "/"))

    def create_message_group(self, group_unique_id: bytes) -> None:
        base_64_id = self._filevalid_base64_encoded(group_unique_id)
        # Create a folder within userdata for the group
        user_data_folder = os.path.abspath(os.path.join(os.getcwd(), "user_data"))
        group_path = os.path.join(user_data_folder, base_64_id)
        os.makedirs(group_path, exist_ok=False)
        # Create a file to store: Message DHT, Public key and IP table, and the group setting table
        message_dht_file = os.path.join(group_path, "message_dht.json")
        public_key_file = os.path.join(group_path, "user_table.json")
        group_setting_file = os.path.join(group_path, "group_setting.json")

        # Initialize the files with empty content
        with open(message_dht_file, "w") as f:
            f.write("{}")
        with open(public_key_file, "w") as f:
            f.write("{}")
        with open(group_setting_file, "w") as f:
            f.write("{}")

        self.MESSAGE_GROUPS[group_unique_id] = group_path

    def delete_local_group_message(self, group_unique_id: bytes) -> None:
        base_64_id = self._filevalid_base64_encoded(group_unique_id)
        # Create a folder within userdata for the group
        user_data_folder = os.path.abspath(os.path.join(os.getcwd(), "user_data"))
        group_path = os.path.join(user_data_folder, base_64_id)

        # Recursively delete the group folder and its contents using python
        # os.system(f"rm -rf {group_path}")
        shutil.rmtree(group_path)
        self.MESSAGE_GROUPS.pop(group_unique_id)
