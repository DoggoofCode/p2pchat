import os
import unittest

from p2pchat.encryption.rsa_message_encrypt import (
    create_message_wrapper,
    decode_message_wrapper,
)


class TestAES(unittest.TestCase):
    def test_encrypt_decrypt(self):
        set_group_id = os.urandom(16)
        message = create_message_wrapper(
            [
                (b"goon", "txt"),
            ],
            b"ved",
            "mrat",
            set_group_id,
        )
        decoded_message = decode_message_wrapper(message.json)
        self.assertEqual(decoded_message["group_id"], set_group_id)
        self.assertIsNotNone(decoded_message)
