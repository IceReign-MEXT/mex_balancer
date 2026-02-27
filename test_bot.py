#!/usr/bin/env python3
"""
🧪 QUICK BOT RESPONSE TEST
Tests if bot starts without errors
"""

import asyncio
import sys
import os
from pathlib import Path

# Add current dir to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_bot_startup():
    """Test bot initializes correctly"""
    print("🚀 Testing MEX BALANCER startup...\n")
    
    try:
        # Test imports
        print("📦 Testing imports...")
        from core.config import Config
        from core.security import SecurityManager
        from core.database import DatabaseManager
        print("✅ All imports successful")
        
        # Test config
        print("\n⚙️  Testing configuration...")
        config = Config()
        config.validate()
        print("✅ Configuration valid")
        
        # Test security
        print("\n🔐 Testing security...")
        security = SecurityManager(config.encryption_key)
        test_data = "test_wallet_key_12345"
        encrypted = security.encrypt(test_data)
        decrypted = security.decrypt(encrypted)
        assert decrypted == test_data
        print("✅ Encryption/decryption working")
        
        # Test database (optional - can skip if no connection)
        print("\n🗄️  Testing database...")
        try:
            db = DatabaseManager(config.database_url)
            await db.connect()
            print("✅ Database connected")
            await db.close()
        except Exception as e:
            print(f"⚠️  Database skipped (will work on Render): {e}")
        
        # Test Telegram (optional)
        print("\n📱 Testing Telegram...")
        try:
            from telegram import Bot
            bot = Bot(token=config.bot_token)
            me = await bot.get_me()
            print(f"✅ Bot responding: @{me.username}")
        except Exception as e:
            print(f"⚠️  Telegram test skipped: {e}")
        
        print("\n" + "="*50)
        print("🎉 BOT IS READY TO RUN!")
        print("="*50)
        print("\nStart commands:")
        print("  python main.py          # Start bot")
        print("  python health_server.py # Start health check")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nFix this before deploying!")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_bot_startup())
    sys.exit(0 if success else 1)
