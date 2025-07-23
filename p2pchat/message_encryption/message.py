import pickle
import datetime
from typing import Literal
from hashlib import sha256
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey, RSAPrivateKey

from cryptography.hazmat.primitives.asymmetric import padding as asymmetric_padding
from cryptography.hazmat.primitives import hashes, serialization

from p2pchat.message_encryption.encryption_keys import aes_encrypt, aes_decrypt

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
        self.message_data = message_type
        self.hash = message_type.hash
        self.AES_key: bytes = b''
        self.AES_iv:bytes = b''
        self.message_data: bytes = self.encrypt(encryption_key)

    def encrypt(self, public_encryption_keys: RSAPublicKey) -> bytes:
        message_bytes: bytes = pickle.dumps(self.message_data)
        print(f"Encrypting {message_bytes.hex()[:10]}...")
        cipher_text, key, iv = aes_encrypt(message_bytes)

        encrypted_AES_ciphertext = public_encryption_keys.encrypt(
            key,
            asymmetric_padding.OAEP(
                mgf=asymmetric_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        self.AES_key = encrypted_AES_ciphertext
        self.AES_iv = iv
        return cipher_text

    def decrypt(self, private_encryption_key: RSAPrivateKey) -> None:
        decrypted_AES_key = private_encryption_key.decrypt(
            self.AES_key,
            asymmetric_padding.OAEP(
                mgf=asymmetric_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        plain_text = aes_decrypt(self.message_data, decrypted_AES_key, self.AES_iv)
        print(f"Encrypting {plain_text.hex()[:10]}...")
        self.message_data = pickle.loads(plain_text)

    def serialize(self) -> bytes:
        return pickle.dumps(self)

    @staticmethod
    def deserialize(data: bytes):
        return pickle.loads(data)

    def __repr__(self):
        return f"MessagePacket({self.message_data})"


