import hashlib
import os
import unittest
from os import path

from p2pchat.encryption.rsa_encryption import verify
from p2pchat.encryption.rsa_message_encrypt import rsa_sign, rsa_verify_signature


class TestRSAEncryption(unittest.TestCase):
    def test_rsa_signing(self):
        public_keys_file = path.abspath(
            path.join(os.getcwd(), "user_data", "keys", "public_key.pem")
        )
        private_key_file = path.abspath(
            path.join(os.getcwd(), "user_data", "keys", "private_key.pem")
        )
        keys = verify(public_keys_file, private_key_file)
        message = hashlib.sha256(b"Hello, world!").digest()
        signature = rsa_sign(message, keys)
        self.assertTrue(rsa_verify_signature(message, signature, keys.public_key))
