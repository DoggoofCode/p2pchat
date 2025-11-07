import base64
import datetime
import json as jsonify
from hashlib import sha256
from typing import Literal, override

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

from p2pchat.encryption.aes_encryption import aes_decrypt, aes_encrypt
from p2pchat.encryption.rsa_encryption import get_rsa_key
from p2pchat.encryption.rsastructs import RSAEncryptionKeys

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
        self.data_hash: bytes = data_hash  # Hash of unencrypted data

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
        artifacts: list[Artifact],
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
        self.artifacts: list[Artifact] = artifacts

    @property
    def dict(self) -> dict:
        return {
            "message_type": self.message_type,
            "time_stamp": self.time_stamp,
            "author": base64.b64encode(self.author).decode("utf-8"),
            "artifact": [artifact.dict for artifact in self.artifacts],
            "ref_hash": base64.b64encode(self.ref_hash).decode("utf-8")
            if self.ref_hash
            else None,
            "headers": {},
        }


class MessageWrapper:
    def __init__(
        self,
        message_hash: bytes,
        message: Message,
        aes_key: bytes,
        iv: bytes,
    ) -> None:
        self.message_hash: bytes = message_hash
        self.message: Message = message
        self.aes_key: bytes = aes_key
        self.aes_iv: bytes = iv
        self.signature: None = None

    @property
    def json(self):
        return jsonify.dumps(
            {
                "message_hash": base64.b64encode(self.message_hash).decode("utf-8"),
                "message": self.message.dict,
                "aes_key": base64.b64encode(self.aes_key).decode("utf-8"),
                "iv": base64.b64encode(self.aes_iv).decode("utf-8"),
                "signature": base64.b64encode(self.signature).decode("utf-8")
                if self.signature
                else None,
            }
        )


def create_message_wrapper(
    artifacts_data: list[tuple[bytes, str]], author: bytes, message_type: MESSAGE_TYPES
) -> MessageWrapper:
    rsa_keys: RSAEncryptionKeys = get_rsa_key()
    artifacts: list[Artifact] = []
    combined_hash: bytes = b""
    common_aes_key: bytes = b""
    common_iv: bytes = b""

    # Get and encrypt artifact data
    for artifact_data in artifacts_data:
        cipher_text, common_aes_key, common_iv = aes_encrypt(
            artifact_data[0],
            common_aes_key if common_aes_key else None,
            common_iv if common_iv else None,
        )
        combined_hash += sha256(artifact_data[0]).digest()
        artifacts.append(
            Artifact(cipher_text, artifact_data[1], sha256(artifact_data[0]).digest())
        )

    # Create message class
    message = Message(
        message_type,
        datetime.datetime.now(),
        author=author,
        artifacts=artifacts,
    )
    # Send message wrapper
    return MessageWrapper(
        sha256(combined_hash).digest(),
        message,
        rsa_encrypt_message(common_aes_key, rsa_keys),
        common_iv,
    )


def decode_message_wrapper(
    json_data: str,
) -> dict:
    # TODO: Verify hash and signature

    rsa_keys: RSAEncryptionKeys = get_rsa_key()
    packet_data: dict = jsonify.loads(json_data)
    decrypted_aes_key = rsa_decrypt_message(
        base64.b64decode(packet_data["aes_key"]), rsa_keys
    )
    artifacts = [
        {
            "data": aes_decrypt(
                base64.b64decode(art["data"]),
                decrypted_aes_key,
                base64.b64decode(packet_data["iv"]),
            ),
            "data_type": art["data_type"],
        }
        for art in packet_data["message"]["artifact"]
    ]
    return {
        "message_type": packet_data["message"]["message_type"],
        "time_stamp": datetime.datetime.fromtimestamp(
            int(packet_data["message"]["time_stamp"])
        ),
        "author": base64.b64decode(packet_data["message"]["author"]).decode("utf-8"),
        "ref-hash": None
        if not packet_data["message"]["ref_hash"]
        else base64.b64decode(packet_data["message"]["ref_hash"]).decode("utf-8"),
        "headers": packet_data["message"]["headers"],
        "artifact": artifacts,
    }
