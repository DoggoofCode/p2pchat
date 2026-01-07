import unittest

from p2pchat.encryption.rsa_message_encrypt import (
    create_message_wrapper,
    decode_message_wrapper,
)


class TestAES(unittest.TestCase):
    def test_encrypt_decrypt(self):
        message = create_message_wrapper(
            [
                (b"goon", "txt"),
            ],
            b"ved",
            "mrat",
        )
        decoded_message = decode_message_wrapper(message.json)
        self.assertIsNotNone(decoded_message)
