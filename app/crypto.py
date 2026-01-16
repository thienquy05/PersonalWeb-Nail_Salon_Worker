from cryptography.fernet import Fernet
import os

fernet_key = os.getenv("FERNET_KEY")
if fernet_key is None:
    raise ValueError("FERNET_KEY environment variable is not set")
fernet = Fernet(fernet_key.encode())

def encrypt(text: str) -> str:
    return fernet.encrypt(text.encode()).decode()

def decrypt(token: str) -> str:
    return fernet.decrypt(token.encode()).decode()