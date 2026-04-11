import base64
import json
import os
import queue
import shutil
import threading
import asyncio as aio

from p2pchat.encryption.rsa_message_encrypt import (
    create_message_wrapper,
    decode_message_wrapper,
)
from p2pchat.packet.packet_communicator import PacketGateway
from p2pchat.response.message_group import GrpFiles


class Responder:
    MESSAGE_GROUPS: dict[bytes, str] = {}
    MESSAGE_GROUPS_LOGS: list[GrpFiles] = []

    def __init__(
        self,
        shutdown_callback: threading.Event,
        output_queue: queue.Queue,
        comm: PacketGateway | None,
    ) -> None:
        self.shut_down_callback = shutdown_callback
        self.output_queue = output_queue
        if comm is None:
            self.comm = None
        else:
            self.comm = comm
            self.responder_thread = threading.Thread(
                target=self._response_loop,
            )
            self.responder_thread.start()
            self.promised_responses: dict[tuple[bytes, bytes], aio.Future] = {}
            self.loop = aio.get_running_loop()  

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
        group_path = os.path.join(user_data_folder, "user_groups", base_64_id)
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

        self.MESSAGE_GROUPS_LOGS.append(GrpFiles(filepath=group_path))
        self.MESSAGE_GROUPS[group_unique_id] = group_path

    def delete_local_group_message(self, group_unique_id: bytes) -> None:
        base_64_id = self._filevalid_base64_encoded(group_unique_id)
        # Create a folder within userdata for the group
        user_data_folder = os.path.abspath(os.path.join(os.getcwd(), "user_data"))
        group_path = os.path.join(user_data_folder, "user_groups", base_64_id)

        # Recursively delete the group folder and its contents using python
        shutil.rmtree(group_path)
        self.MESSAGE_GROUPS.pop(group_unique_id)

    def _index_local_group_message(self) -> None:
        # Index all local groups
        group_paths = os.walk(os.path.join(os.getcwd(), "user_data", "user_groups"))
        for group_path in group_paths:
            if group_path[0].split("/")[-1] == "user_groups":
                continue
            group_unique_id = self._filevalid_base64_decode(
                group_path[0].split("/")[-1]
            )
            self.MESSAGE_GROUPS_LOGS.append(GrpFiles(filepath=group_path[0]))
            self.MESSAGE_GROUPS[group_unique_id] = group_path[0]

    def _response_loop(self) -> None:
        self._index_local_group_message()
        while not self.shut_down_callback.is_set():
            try:
                message = self.output_queue.get(timeout=0.5)
                self._process_message(message)
            except queue.Empty:
                continue

        # Clean up any remaining messages in the queue
        while not self.output_queue.empty():
            self.output_queue.get()

    def _message_ratification(self, original_json, inner_message):
        # TODO: Check own position in the group (ratifier / user)
        pass

    def _message_identifier(self, original_json, inner_message):
        pass        
        
    # TODO: Create allow sending real message
    async def send_message_identifier(self):
        # Create promise in response routine
        future = aio.get_running_loop().create_future()
        message = create_message_wrapper(
            [(b"I WANT A REPONSE", "text/markdown")],
            "mrat",
            b"\x00",            
            b"\x00",
            ref_hash=b""
        )
        self.comm.send(message.json.encode())
        self.promised_responses[(message.message_hash, message.message.group_id)] = future  # register first
        await self.promised_responses[(message.message_hash, message.message.group_id)]
        return future.result()

    

    def _response_routine_handler(self, original_json, inner_message):
        # Ref hash _then_ group id
        packet_id = (inner_message["ref-hash"], inner_message["group_id"])
        if packet_id in self.promised_responses:
            future = self.promised_responses.pop(packet_id)
            self.loop.call_soon_threadsafe(future.set_result, original_json)
        else:
            print(f"Whoops, no handler found for {inner_message}")

    def _message_ratification(self, original_json, inner_message):
        message = create_message_wrapper(
            [(b"you got your response diddyblud", "text/markdown")],
            "mratR",
            b"\x00",            
            b"\x00",
            ref_hash=base64.b64decode(original_json["message_hash"])
        )
        self.comm.send(message.json.encode())

    def _message_ratification_response(self, original_json, inner_message):
        # Implement message ratification response logic here
        pass

    def _process_message(self, message: bytes) -> None:
        # Only message packets (green fn)
        original_json = json.loads(message.decode())
        inner_message = decode_message_wrapper(message.decode())
        message_type = inner_message["message_type"]
        if message_type == "mrat":
            self._message_ratification(original_json, inner_message)
        elif message_type == "i":
            self._message_identifier(original_json, inner_message)
        elif message_type == "iR":
            pass
        elif message_type[-1] == 'R':
            self._response_routine_handler(original_json, inner_message)
        else:
            raise ValueError(f"Unknown message type: {inner_message['message_type']}")
