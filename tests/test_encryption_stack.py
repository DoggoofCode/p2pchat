import os
import unittest
from os import path

from p2pchat.encryption.aes_encryption import aes_decrypt, aes_encrypt
from p2pchat.encryption.rsa_encryption import verify
from p2pchat.encryption.rsa_message_encrypt import (
    rsa_decrypt_message,
    rsa_encrypt_message,
)
from p2pchat.encryption.rsastructs import RSAEncryptionKeys


class TestRSAEncryption(unittest.TestCase):
    def test_generate_key_pair(self):
        public_keys_file = path.abspath(
            path.join(os.getcwd(), "user_data", "keys", "public_key.pem")
        )
        private_key_file = path.abspath(
            path.join(os.getcwd(), "user_data", "keys", "private_key.pem")
        )

        keys: RSAEncryptionKeys = verify(
            public_keys_file.replace(r"/Users/vedjaggi", "~"),
            private_key_file.replace(r"/Users/vedjaggi", "~"),
        )

        original_text = b"Goon"
        cipher_text, aes_key, iv = aes_encrypt(original_text)
        encrypted_key = rsa_encrypt_message(aes_key, keys)
        decrypted_aes_key = rsa_decrypt_message(encrypted_key, keys)
        complete_decrypted_text = aes_decrypt(cipher_text, decrypted_aes_key, iv)

        self.assertEqual(complete_decrypted_text, original_text)
