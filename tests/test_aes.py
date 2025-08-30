import unittest
from p2pchat.encryption.aes_encryption import aes_encrypt, aes_decrypt

class TestAES(unittest.TestCase):
    def test_encrypt_decrypt(self):
        plaintext = b"Test123!\xff"
        ciphertext, key, iv = aes_encrypt(plaintext)
        decrypted_text = aes_decrypt(ciphertext, key, iv)
        self.assertEqual(decrypted_text, plaintext)
