from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey, RSAPrivateKey

class RSAEncryptionKeys:
    def __init__(self, public_key: RSAPublicKey, private_key: RSAPrivateKey) -> None:
        self.public_key = public_key
        self.private_key = private_key

    def __repr__(self):
        return f"RSAEncryptionKeys(public_key={self.public_key}, private_key={self.private_key})"


