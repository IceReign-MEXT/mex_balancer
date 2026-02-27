"""Security and encryption"""
from cryptography.fernet import Fernet
import hashlib
import hmac
import base58
from solders.keypair import Keypair

class SecurityManager:
    def __init__(self, encryption_key: str):
        # Ensure key is proper length for Fernet
        key_bytes = encryption_key.encode()
        if len(key_bytes) < 32:
            key_bytes = key_bytes.ljust(32, b'0')
        elif len(key_bytes) > 32:
            key_bytes = key_bytes[:32]
        
        # Base64 encode for Fernet
        import base64
        key_b64 = base64.urlsafe_b64encode(key_bytes)
        self.cipher = Fernet(key_b64)
    
    def encrypt(self, data: str) -> str:
        """Encrypt sensitive data"""
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted: str) -> str:
        """Decrypt data"""
        return self.cipher.decrypt(encrypted.encode()).decode()
    
    def validate_solana_address(self, address: str) -> bool:
        """Validate Solana address format"""
        try:
            decoded = base58.b58decode(address)
            return len(decoded) == 32
        except:
            return False
    
    def generate_signature(self, data: str, secret: str) -> str:
        """Generate HMAC signature"""
        return hmac.new(
            secret.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
