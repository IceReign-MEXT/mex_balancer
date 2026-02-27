from solders.keypair import Keypair

key = "FctWuo6HVMywsXSByra2gFYnpeD8SYtmmfnTV8P1tgyb"

try:
    wallet = Keypair.from_base58_string(key)
    print(f"✅ Wallet valid!")
    print(f"Address: {wallet.pubkey()}")
    print(f"Key length: {len(key)} chars")
except Exception as e:
    print(f"❌ Error: {e}")
