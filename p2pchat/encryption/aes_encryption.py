# AES Encryption
from os import urandom

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

block_size: int = algorithms.AES.block_size  # pyright: ignore[reportAssignmentType]


def aes_encrypt(
    plaintext: bytes,
    userset_AES_key: bytes | None = None,
    userset_iv: bytes | None = None,
) -> tuple[bytes, bytes, bytes]:
    AES_key: bytes = urandom(32) if userset_AES_key is None else userset_AES_key
    iv: bytes = urandom(16) if userset_iv is None else userset_iv

    padder = padding.PKCS7(block_size).padder()
    padded_plaintext = padder.update(plaintext) + padder.finalize()

    cipher = Cipher(algorithms.AES(AES_key), modes.CBC(iv), backend=default_backend())

    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_plaintext) + encryptor.finalize()

    return ciphertext, AES_key, iv


def aes_decrypt(ciphertext: bytes, key: bytes, iv: bytes) -> bytes:
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()

    unpadder = padding.PKCS7(block_size).unpadder()
    plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()

    return plaintext
