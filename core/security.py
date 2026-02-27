import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

class WarlordSecurity:
    def __init__(self):
        key = os.getenv("ENCRYPTION_KEY")
        if not key:
            key = Fernet.generate_key().decode()
        try:
            self.cipher = Fernet(key.encode())
        except:
            self.cipher = Fernet(Fernet.generate_key())

    def encrypt_data(self, data: str) -> str:
        return self.cipher.encrypt(data.encode()).decode()

    def decrypt_data(self, token: str) -> str:
        return self.cipher.decrypt(token.encode()).decode()

security = WarlordSecurity()
