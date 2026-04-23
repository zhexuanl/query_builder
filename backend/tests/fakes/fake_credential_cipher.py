import base64

from domain.interfaces.credential_cipher import ICredentialCipher


class FakeCredentialCipher(ICredentialCipher):
    """Base64-encodes instead of encrypting — predictable for tests."""

    def encrypt(self, plaintext: str) -> bytes:
        return base64.b64encode(plaintext.encode())

    def decrypt(self, ciphertext: bytes) -> str:
        return base64.b64decode(ciphertext).decode()
