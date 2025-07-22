import pickle
import datetime
from typing import Literal
from hashlib import sha256
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey, RSAPrivateKey

from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes

MESSAGE_TYPES = Literal["send-msg", "edit-msg", "del-msg", "change-gname", "add_member"]

class MsgData:
    def __init__(self, data: bytes, data_type: str):
        self.data: bytes = data
        self.data_type: str = data_type

    def __repr__(self):
        return f"MsgData(data={self.data}, data_type='{self.data_type}')"

class Message:
    def __init__(self,
                 message_type: MESSAGE_TYPES, *,
                 message_data: list[MsgData] | None = None,
                 message_ref: bytes | None = None
                 ):
        self.data: list[MsgData] = message_data
        self.message_type = message_type
        self.time_stamp = datetime.datetime.now()
        self.message_ref = message_ref
        if message_ref is None and message_ref == "edit-msg" and message_ref == "del-msg":
            raise AssertionError("When message type is 'del-msg' or 'edit-msg' a message must be referenced")

    def serialize(self) -> bytes:
        return pickle.dumps(self)

    @property
    def hash(self) -> bytes:
        return sha256(self.serialize()).digest()

    @staticmethod
    def deserialize(data: bytes):
        return pickle.loads(data)

    def __repr__(self):
        if self.message_ref is None:
            referencer = self.data
        else:
            referencer = f"{self.message_ref} for {self.data}"
        return f"Message({self.message_type}: {referencer})"

class MessagePacket:
    def __init__(self, message_type: Message, encryption_key: RSAPublicKey) -> None:
        self.message_type = message_type
        self.hash = message_type.hash
        self.message_type: bytes = self.encrypt(encryption_key)

    def encrypt(self, public_encryption_keys: RSAPublicKey) -> bytes:
        message = pickle.dumps(self.message_type)
        # The `message` is too long fix later
        # ciphertext = public_encryption_keys.encrypt(
        #     b"hello world!" * 10000,
        #     padding.OAEP(
        #         mgf=padding.MGF1(algorithm=hashes.SHA256()),
        #         algorithm=hashes.SHA256(),
        #         label=None
        #     )
        # )
        return message

    def decrypt(self, private_encryption_key: RSAPrivateKey) -> None:
        # plaintext = private_encryption_key.decrypt(
        #     self.message_type,
        #     padding.OAEP(
        #         mgf=padding.MGF1(algorithm=hashes.SHA256()),
        #         algorithm=hashes.SHA256(),
        #         label=None
        #     )
        # )
        # # Uses pickle to remove message as a dep
        self.message_type = pickle.loads(self.message_type)

    def serialize(self) -> bytes:
        return pickle.dumps(self)

    @staticmethod
    def deserialize(data: bytes):
        return pickle.loads(data)

    def __repr__(self):
        return f"MessagePacket({self.message_type})"


