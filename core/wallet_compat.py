"""Wallet compatibility - uses real solders or falls back"""
try:
    from solders.keypair import Keypair
    from solders.pubkey import Pubkey
    SOLDERS_AVAILABLE = True
except ImportError:
    SOLDERS_AVAILABLE = False
    print("⚠️  Solders not available - using fallback")

if SOLDERS_AVAILABLE:
    class Wallet:
        def __init__(self, key: str):
            self.keypair = Keypair.from_base58_string(key)
            self.pubkey = str(self.keypair.pubkey())
        
        def sign(self, message: bytes) -> bytes:
            return self.keypair.sign_message(message)
else:
    # Fallback stub for testing
    class Wallet:
        def __init__(self, key: str):
            self.pubkey = "FctWuo6HVMywsXSByra2gFYnpeD8SYtmmfnTV8P1tgyb"
        
        def sign(self, message: bytes) -> bytes:
            return b"stub_signature"

__all__ = ['Wallet', 'SOLDERS_AVAILABLE']
