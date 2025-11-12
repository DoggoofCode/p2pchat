import os
import unittest
from os import path

from p2pchat.encryption.rsa_encryption import create_keys, read_keys


class TestRSAEncryption(unittest.TestCase):
    def test_generate_key_pair(self):
        public_keys_file = path.abspath(
            path.join(os.getcwd(), "user_data", "keys", "public_key.pem")
        )
        private_key_file = path.abspath(
            path.join(os.getcwd(), "user_data", "keys", "private_key.pem")
        )
        create_keys(public_keys_file, private_key_file)
        self.assertTrue(os.path.exists(public_keys_file))
        self.assertTrue(os.path.exists(private_key_file))

    def test_read_keys(self):
        public_keys_file = path.abspath(
            path.join(os.getcwd(), "user_data", "keys", "public_key.pem")
        )
        private_key_file = path.abspath(
            path.join(os.getcwd(), "user_data", "keys", "private_key.pem")
        )
        create_keys(public_keys_file, private_key_file)
        self.assertTrue(os.path.exists(public_keys_file))
        self.assertTrue(os.path.exists(private_key_file))
        self.assertIsNotNone(read_keys(public_keys_file, private_key_file))
