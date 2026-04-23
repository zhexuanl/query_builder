from abc import ABC, abstractmethod


class ICredentialCipher(ABC):
    @abstractmethod
    def encrypt(self, plaintext: str) -> bytes: ...

    @abstractmethod
    def decrypt(self, ciphertext: bytes) -> str: ...
