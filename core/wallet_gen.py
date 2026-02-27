import os, sys, json
import base58
from cryptography.hazmat.primitives.asymmetric import ed25519
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.security import security

def generate_sniper_wallet():
    # Generate a standard Ed25519 key (Solana standard) without solders
    priv_key_obj = ed25519.Ed25519PrivateKey.generate()
    pub_key_obj = priv_key_obj.public_key()
    
    # Format for Solana
    raw_priv = priv_key_obj.private_bytes_raw()
    raw_pub = pub_key_obj.public_bytes_raw()
    
    # Combined secret (Solana format is 64 bytes: private + public)
    secret_key = raw_priv + raw_pub
    
    pub_address = base58.b58encode(raw_pub).decode()
    priv_string = str(list(secret_key))
    
    # Encrypt for the vault
    encrypted_key = security.encrypt_data(priv_string)
    
    print(f"\n🎯 **SNIPER WALLET GENERATED (LITE MODE)**")
    print(f"Public Address: {pub_address}")
    print(f"------------------------------------")
    print(f"⚠️ ACTION: Send 0.1 SOL to this address.")
    print(f"------------------------------------")
    
    with open("core/.secret_vault", "w") as f:
        f.write(f"{pub_address}:{encrypted_key}")

if __name__ == "__main__":
    generate_sniper_wallet()
