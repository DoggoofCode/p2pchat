import os
import unittest

from p2pchat.response.responder import Responder


class TestGroupCreation(unittest.TestCase):
    def test_encrypt_decrypt(self):
        responder = Responder()
        group_id = os.urandom(16)
        responder.create_message_group(group_id)
        # Save group path
        group_path = responder[group_id]
        self.assertTrue(
            os.path.exists(os.path.join(os.getcwd(), "user_data", group_path))
        )
        responder.delete_local_group_message(group_id)
        self.assertFalse(
            os.path.exists(os.path.join(os.getcwd(), "user_data", group_path))
        )
