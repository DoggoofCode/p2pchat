# AES Encryption
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from os import urandom
block_size: int = algorithms.AES.block_size  # type: ignore

def aes_encrypt(plaintext: bytes) -> tuple[bytes, bytes, bytes]:
    AES_key: bytes = urandom(32)
    iv: bytes = urandom(16)

    padder = padding.PKCS7(block_size).padder()
    padded_plaintext = padder.update(plaintext) + padder.finalize()

    cipher = Cipher(algorithms.AES(AES_key), modes.CBC(iv), backend=default_backend())

    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_plaintext) + encryptor.finalize()

    return ciphertext, AES_key, iv

def aes_decrypt(ciphertext: bytes, key:bytes, iv:bytes) -> bytes:
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()

    unpadder = padding.PKCS7(block_size).unpadder()
    plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()

    return plaintext

if __name__ == "__main__":
    print("===Testing AES Encryption===")
    plaintext = b"Hello, World!"
    ciphertext, key, iv = aes_encrypt(plaintext)
    decrypted_text = aes_decrypt(ciphertext, key, iv)
    print(f"Original Text: {plaintext}")
    print(f"Encrypted Text: {ciphertext}")
    print(f"Decrypted Text: {decrypted_text}")
