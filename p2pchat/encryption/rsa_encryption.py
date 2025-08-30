# RSA Encryption
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey, RSAPrivateKey
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.types import PrivateKeyTypes, PublicKeyTypes

from typing import cast
from os import path
import os

class RSAEncryptionKeys:
    def __init__(self, public_key: RSAPublicKey, private_key: RSAPrivateKey | PrivateKeyTypes) -> None:
        self.public_key = public_key
        self.private_key = private_key

    def __repr__(self):
        return f"RSAEncryptionKeys(public_key={self.public_key}, private_key={self.private_key})"

def create_keys(public_keys_file: str, private_key_file: str):
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    # Public Key
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    line_data = public_pem.splitlines()

    # Create directories if they don't exist
    os.makedirs(os.path.dirname(public_keys_file), exist_ok=True)
    os.makedirs(os.path.dirname(private_key_file), exist_ok=True)

    # Exist if the file already exists
    if not os.path.exists(public_keys_file):
        # Public Key
        with open(public_keys_file, "wb") as key_file:
            for line in line_data:
                key_file.write(line)

    # Generate the private key (assuming you already have this part)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    )
    if not os.path.exists(private_key_file):
        # Write the private key to the file
        with open(private_key_file, "wb") as key_file:
            key_file.write(private_pem)

def read_keys(public_keys_file: str, private_key_file: str) -> RSAEncryptionKeys:
    with open(public_keys_file, "rb") as key_file:
        public_key: PublicKeyTypes = serialization.load_pem_public_key(
            key_file.read(),
        )
    with open(private_key_file, "rb") as key_file:
        private_key: PrivateKeyTypes = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
        )
    return RSAEncryptionKeys(
        cast(rsa.RSAPublicKey, public_key),
        cast(rsa.RSAPrivateKey, private_key)
    )

def verify(public_keys_file: str, private_key_file: str) -> RSAEncryptionKeys:
    try:
        keys = read_keys(public_keys_file, private_key_file)
        return keys
    except FileNotFoundError:
        create_keys(public_keys_file, private_key_file)
        keys = read_keys(public_keys_file, private_key_file)
        return keys


if __name__ == "__main__":
    print("===Testing RSA Encryption===")
    public_keys_file = path.abspath(path.join(os.getcwd(), "user_data", "keys", "public_keys.pem"))
    private_key_file = path.abspath(path.join(os.getcwd(), "user_data", "keys", "private_key.pem"))
    create_keys(public_keys_file, private_key_file)
    print(read_keys(public_keys_file, private_key_file))
