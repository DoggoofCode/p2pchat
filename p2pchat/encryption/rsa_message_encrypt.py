import datetime
from typing import Literal, override

# from hashlib import sha256
from p2pchat.encryption.rsa_encryption import verify
import base64
import json as jsonify

from p2pchat.encryption.rsastructs import RSAEncryptionKeys

from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes

MESSAGE_TYPES = Literal["send-msg", "edit-msg", "del-msg", "change-gname", "add_member"]


def rsa_encrypt_message(information: bytes, keys: RSAEncryptionKeys) -> bytes:
    # TODO: Encrypt chat
    # The `message` is too long fix later
    ciphertext = keys.public_key.encrypt(
        information,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )

    return ciphertext


def rsa_decrypt_message(information: bytes, keys: RSAEncryptionKeys) -> bytes:
    # TODO: Actual Decrypt chat
    plaintext = keys.private_key.decrypt(
        information,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )

    return plaintext


class Artifact:
    def __init__(self, data: bytes, data_type: str, data_hash: bytes):
        self.data: bytes = data
        self.data_type: str = data_type
        self.data_hash: bytes = data_hash

    @override
    def __repr__(self):
        return f"Artifact(data={self.data}, data_type='{self.data_type}')"

    @property
    def dict(self):
        return {
            "data": base64.b64encode(self.data).decode("utf-8"),
            "data_type": self.data_type,
            "data_hash": base64.b64encode(self.data_hash).decode("utf-8"),
        }


class Message:
    def __init__(
        self,
        message_type: MESSAGE_TYPES,
        time_stamp: datetime.datetime,
        author: bytes,
        artifact: Artifact,
        ref_hash: bytes | None = None,
    ) -> None:
        if not author:
            raise ValueError("Author cannot be empty")
        if ref_hash and not (message_type == "edit-msg" or message_type == "del-msg"):
            raise ValueError(
                "Ref hash must not be used when message type is not edit-msg or del-msg"
            )
        if not ref_hash and (message_type == "edit-msg" or message_type == "del-msg"):
            raise ValueError(f"Ref hash must be bytes for {message_type}")
        self.message_type: MESSAGE_TYPES = message_type
        self.ref_hash: bytes | None = ref_hash
        self.time_stamp: int = int(time_stamp.timestamp())
        self.author: bytes = author
        self.artifact: Artifact = artifact

    @property
    def dict(self):
        return {
            "message_type": self.message_type,
            "time_stamp": self.time_stamp,
            "author": base64.b64encode(self.author).decode("utf-8"),
            "artifact": self.artifact.dict,
            "ref_hash": base64.b64encode(self.ref_hash).decode("utf-8")
            if self.ref_hash
            else None,
        }


class MessageWrapper:
    def __init__(
        self,
        message_hash: bytes,
        message: Message,
    ) -> None:
        self.message_hash: bytes = message_hash
        self.message: Message = message

    @property
    def json(self):
        return jsonify.dumps(
            {
                "message_hash": base64.b64encode(self.message_hash).decode("utf-8"),
                "message": self.message.dict,
            }
        )


# class MsgData:
#     def __init__(self, data: bytes, data_type: str):
#         self.data: bytes = data
#         self.data_type: str = data_type

#     def __repr__(self):
#         return f"MsgData(data={self.data}, data_type='{self.data_type}')"


# class Message:
#     def __init__(self,
#         message_type: MESSAGE_TYPES,
#         *,
#         message_data: list[MsgData],
#         message_ref: bytes | None = None,
#     ):
#         self.data: list[MsgData] = message_data
#         self.message_type = message_type
#         self.time_stamp = datetime.datetime.now()
#         self.message_ref = message_ref
#         if (
#             message_ref is None
#             and message_type == "edit-msg"
#             and message_type == "del-msg"
#         ):
#             raise AssertionError(
#                 "When when type is 'del-msg' or 'edit-msg' a message must be referenced"
#             )

# def serialize(self) -> bytes:
#     return pickle.dumps(self)

# @property
# def hash(self) -> bytes:
#     return sha256(self.serialize()).digest()

# @staticmethod
# def deserialize(data: bytes):
#     return pickle.loads(data)

# def __repr__(self):
#     if self.message_ref is None:
#         referencer = self.data
#     else:
#         referencer = f"{self.message_ref} for {self.data}"
#     return f"Message({self.message_type}: {referencer})"


# class MessagePacket:
#     def __init__(self, message_type: Message, encryption_key: RSAPublicKey) -> None:
#         self.message_type: Message = message_type
#         self.hash = message_type.hash
#         self.message_type: bytes = self.encrypt(encryption_key)

#     def encrypt(self, public_encryption_keys: RSAPublicKey) -> bytes:
#         message = pickle.dumps(self.message_type)
#         # TODO: Encrypt chat
#         # The `message` is too long fix later
#         # ciphertext = public_encryption_keys.encrypt(
#         #     b"hello world!" * 10000,
#         #     padding.OAEP(
#         #         mgf=padding.MGF1(algorithm=hashes.SHA256()),
#         #         algorithm=hashes.SHA256(),
#         #         label=None
#         #     )
#         # )
#         return message

#     def decrypt(self, private_encryption_key: RSAPrivateKey) -> None:
#         # TODO: Actual Decrypt chat
#         # plaintext = private_encryption_key.decrypt(
#         #     self.message_type,
#         #     padding.OAEP(
#         #         mgf=padding.MGF1(algorithm=hashes.SHA256()),
#         #         algorithm=hashes.SHA256(),
#         #         label=None
#         #     )
#         # )
#         # # Uses pickle to remove message as a dep
#         self.message_type = pickle.loads(self.message_type)

#     def serialize(self) -> bytes:
#         return pickle.dumps(self)

#     @staticmethod
#     def deserialize(data: bytes):
#         return pickle.loads(data)

#     def __repr__(self):
#         return f"MessagePacket({self.message_type})"
