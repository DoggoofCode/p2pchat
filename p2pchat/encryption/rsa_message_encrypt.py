import base64
import datetime
import json as jsonify
from hashlib import sha256
from typing import Literal, override

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, utils
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey

from p2pchat.encryption.aes_encryption import aes_decrypt, aes_encrypt
from p2pchat.encryption.rsa_encryption import get_rsa_key
from p2pchat.encryption.rsastructs import RSAEncryptionKeys

MESSAGE_TYPES = Literal[
    "i", "iR", "mrat", "mratR", "smsg", "smsgR", "pkt", "pktR", "dht", "dhtR"
]


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


def rsa_sign(information: bytes, keys: RSAEncryptionKeys) -> bytes:
    signed_text = keys.private_key.sign(
        information,
        padding.PSS(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        utils.Prehashed(hashes.SHA256()),
    )

    return signed_text


def rsa_verify_signature(
    information: bytes, signature: bytes, public_key: RSAPublicKey
) -> bool:
    try:
        public_key.verify(
            signature,
            information,
            padding.PSS(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            utils.Prehashed(hashes.SHA256()),
        )
    except InvalidSignature:
        print("pluh")
        return False
    return True


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
        group_id: bytes,
        author: bytes,
        artifacts: list[Artifact],
        ref_hash: bytes | None = None,
    ) -> None:
        if not author:
            raise ValueError("Author cannot be empty")
        self.message_type: MESSAGE_TYPES = message_type
        self.ref_hash: bytes | None = ref_hash
        self.time_stamp: int = int(time_stamp.timestamp())
        self.author: bytes = author
        self.artifacts: list[Artifact] = artifacts
        self.group_id: bytes = group_id

    @property
    def dict(self) -> dict:
        return {
            "message_type": self.message_type,
            "time_stamp": self.time_stamp,
            "author": base64.b64encode(self.author).decode("utf-8"),
            "group_id": base64.b64encode(self.group_id).decode("utf-8"),
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
        prev_message: bytes,
    ) -> None:
        self.message_hash: bytes = message_hash
        self.message: Message = message
        self.aes_key: bytes = aes_key
        self.aes_iv: bytes = iv
        self.prev_message: bytes = prev_message
        self.signature: bytes = rsa_sign(message_hash, get_rsa_key())

    @property
    def json(self):
        return jsonify.dumps(
            {
                "message_hash": base64.b64encode(self.message_hash).decode("utf-8"),
                "prev_message": base64.b64encode(self.prev_message).decode("utf-8"),
                "message": self.message.dict,
                "aes_key": base64.b64encode(self.aes_key).decode("utf-8"),
                "iv": base64.b64encode(self.aes_iv).decode("utf-8"),
                "signature": base64.b64encode(self.signature).decode("utf-8")
                if self.signature
                else None,
            }
        )


def create_message_wrapper(
    artifacts_data: list[tuple[bytes, str]],
    message_type: MESSAGE_TYPES,
    group_id: bytes,
    prev_message: bytes,
    *,
    ref_hash: bytes | None = None
) -> MessageWrapper:
    rsa_keys: RSAEncryptionKeys = get_rsa_key()
    artifacts: list[Artifact] = []
    combined_hash: bytes = b""
    common_aes_key: bytes = b""
    common_iv: bytes = b""

    keys = get_rsa_key()
    author_public_key_bytes = keys.public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

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
        author=author_public_key_bytes,
        artifacts=artifacts,
        group_id=group_id,
        ref_hash = ref_hash
    )
    # Send message wrapper
    return MessageWrapper(
        sha256(combined_hash).digest(),
        message,
        rsa_encrypt_message(common_aes_key, rsa_keys),
        common_iv,
        prev_message,
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

    # Verify hash
    msg_hash = base64.b64decode(packet_data["message_hash"])
    signature = base64.b64decode(packet_data["signature"])
    auth_pub_key_bytes = base64.b64decode(packet_data["message"]["author"])
    loaded_public_key = serialization.load_pem_public_key(auth_pub_key_bytes)
    if not isinstance(loaded_public_key, RSAPublicKey):
        raise ValueError("Invalid public key")
    if not (rsa_verify_signature(msg_hash, signature, loaded_public_key)):
        raise ValueError("Invalid hash")

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
        # "message_hash":msg_hash,
        "message_type": packet_data["message"]["message_type"],
        "time_stamp": datetime.datetime.fromtimestamp(
            int(packet_data["message"]["time_stamp"])
        ),
        "author": base64.b64decode(packet_data["message"]["author"]).decode("utf-8"),
        "ref-hash": None
        if not packet_data["message"]["ref_hash"]
        else base64.b64decode(packet_data["message"]["ref_hash"]),
        "headers": packet_data["message"]["headers"],
        "artifact": artifacts,
        "group_id": base64.b64decode(packet_data["message"]["group_id"]),
    }
