# RSA Encryption
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey, RSAPrivateKey
from cryptography.hazmat.primitives.asymmetric import rsa

# AES Encryption
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from os import urandom

class RSAEncryptionKeys:
    def __init__(self, public_key: RSAPublicKey, private_key: RSAPrivateKey,) -> None:
        self.public_key = public_key
        self.private_key = private_key

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
    with open(public_keys_file, "wb") as key_file:
        for line in line_data:
            key_file.write(line)

    # Private Key
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    )
    line_data = private_pem.splitlines()
    with open(private_key_file, "wb") as key_file:
        for line in line_data:
            key_file.write(line)

def read_keys(public_keys_file: str, private_key_file: str) -> RSAEncryptionKeys:
    with open(public_keys_file, "rb") as key_file:
        public_key: RSAPublicKey = serialization.load_pem_public_key(
            key_file.read(),
        )
    with open(private_key_file, "rb") as key_file:
        private_key: RSAPrivateKey = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
        )
    return RSAEncryptionKeys(public_key, private_key)

def verify(public_keys_file: str, private_key_file: str) -> RSAEncryptionKeys:
    try:
        keys = read_keys(public_keys_file, private_key_file)
        return keys
    except FileNotFoundError:
        create_keys(public_keys_file, private_key_file)
        keys = read_keys(public_keys_file, private_key_file)
        return keys


def aes_encrypt(plaintext: bytes) -> tuple[bytes, bytes, bytes]:
    AES_key: bytes = urandom(32)
    iv: bytes = urandom(16)

    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_plaintext = padder.update(plaintext) + padder.finalize()

    cipher = Cipher(algorithms.AES(AES_key), modes.CBC(iv), backend=default_backend())

    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_plaintext) + encryptor.finalize()

    return ciphertext, AES_key, iv

def aes_decrypt(ciphertext: bytes, key:bytes, iv:bytes) -> bytes:
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()

    unpadder = padding.PKCS7(128).unpadder()
    plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()

    return plaintext
