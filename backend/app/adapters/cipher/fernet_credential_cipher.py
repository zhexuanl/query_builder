from cryptography.fernet import Fernet, InvalidToken

from domain.interfaces.credential_cipher import ICredentialCipher


class FernetCredentialCipher(ICredentialCipher):
    def __init__(self, key: bytes) -> None:
        self._fernet = Fernet(key)

    def encrypt(self, plaintext: str) -> bytes:
        return self._fernet.encrypt(plaintext.encode())

    def decrypt(self, ciphertext: bytes) -> str:
        try:
            return self._fernet.decrypt(ciphertext).decode()
        except InvalidToken as exc:
            raise ValueError("Decryption failed: invalid or tampered ciphertext") from exc
