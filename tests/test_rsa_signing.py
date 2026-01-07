import hashlib
import unittest

from p2pchat.encryption.rsa_encryption import get_rsa_key
from p2pchat.encryption.rsa_message_encrypt import rsa_sign, rsa_verify_signature


class TestRSAEncryption(unittest.TestCase):
    def test_rsa_signing(self):
        keys = get_rsa_key()
        message = hashlib.sha256(b"Hello, world!").digest()
        signature = rsa_sign(message, keys)
        self.assertTrue(rsa_verify_signature(message, signature, keys.public_key))
