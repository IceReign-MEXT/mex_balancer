import sys
import os
import asyncio

# The Absolute Path Fix
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

print(f"📂 Project Root: {BASE_DIR}")

try:
    from core.security import security
    from modules.router import router
    print("✅ Core and Modules linked!")
except ImportError as e:
    print(f"❌ Error: {e}")
    print("\nCheck your files by running 'ls -R' in Termux.")
    sys.exit(1)

async def test():
    print("🛡️ Testing Security Module...")
    # Your NEW key will be tested here
    try:
        secret = "MySecretWalletKey"
        encrypted = security.encrypt_data(secret)
        decrypted = security.decrypt_data(encrypted)
        if secret == decrypted:
            print("✅ Encryption: WORKING")
    except Exception as e:
        print(f"❌ Encryption Error: {e}")

    print("\n📡 Testing Router...")
    res = await router.secure_snipe("DezXAZqz7ccuSpxvA9PjMTG7EwY94VAnK9KREmK")
    print(f"Result: {res}")

if __name__ == "__main__":
    asyncio.run(test())
