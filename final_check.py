#!/usr/bin/env python3
"""
🔥 MEX BALANCER - FINAL PRE-DEPLOY CHECK
Tests every component, shows exactly what's missing
"""

import os
import sys
import asyncio
import subprocess
from pathlib import Path

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def check(section, status, message, critical=True):
    icon = "✅" if status else "❌"
    color = bcolors.OKGREEN if status else bcolors.FAIL
    crit = " [CRITICAL]" if not status and critical else ""
    print(f"{color}{icon} {section:<20} {message}{crit}{bcolors.ENDC}")
    return status

async def run_checks():
    print(f"\n{bcolors.BOLD}{'='*60}")
    print("  MEX BALANCER - FINAL SYSTEM CHECK")
    print(f"{'='*60}{bcolors.ENDC}\n")
    
    all_good = True
    
    # 1. FILES CHECK
    print(f"{bcolors.HEADER}📁 CRITICAL FILES{bcolors.ENDC}")
    files = {
        'main.py': 'Entry point',
        'requirements.txt': 'Dependencies',
        'Procfile': 'Render config',
        'runtime.txt': 'Python version',
        '.env': 'Secrets/Keys',
        'core/config.py': 'Config module',
        'core/sniper.py': 'Trading engine',
        'core/analyzer.py': 'Rug checker',
        'core/database.py': 'Database',
        'core/auto_trader.py': 'Auto-sell',
        'core/security.py': 'Encryption',
    }
    
    for file, desc in files.items():
        exists = Path(file).exists()
        check(file, exists, desc)
        if not exists:
            all_good = False
    
    # 2. ENVIRONMENT VARIABLES
    print(f"\n{bcolors.HEADER}🔐 ENVIRONMENT VARIABLES{bcolors.ENDC}")
    env_vars = ['BOT_TOKEN', 'ADMIN_ID', 'CHANNEL_ID', 'RPC_URL', 
                'RUGCHECK_API_KEY', 'SOL_MAIN', 'ENCRYPTION_KEY', 'DATABASE_URL']
    
    for var in env_vars:
        val = os.getenv(var)
        masked = val[:10] + '...' if val and len(val) > 15 else val
        check(var, bool(val), f"Set: {masked}" if val else "MISSING")
        if not val:
            all_good = False
    
    # 3. PYTHON PACKAGES
    print(f"\n{bcolors.HEADER}📦 PYTHON PACKAGES{bcolors.ENDC}")
    
    packages = {
        'solana': 'Solana RPC',
        'solders': 'Keypair/Transactions',
        'telegram': 'Bot interface',
        'asyncpg': 'PostgreSQL',
        'aiohttp': 'HTTP client',
        'cryptography': 'Encryption',
        'loguru': 'Logging',
    }
    
    for pkg, desc in packages.items():
        try:
            __import__(pkg)
            check(pkg, True, desc)
        except ImportError:
            check(pkg, False, desc)
            all_good = False
    
    # 4. TELEGRAM BOT TEST
    print(f"\n{bcolors.HEADER}📱 TELEGRAM CONNECTION{bcolors.ENDC}")
    try:
        from telegram import Bot
        bot = Bot(os.getenv('BOT_TOKEN'))
        me = await bot.get_me()
        check('Bot Auth', True, f"@{me.username}")
        
        # Test admin
        admin_id = os.getenv('ADMIN_ID')
        if admin_id:
            try:
                chat = await bot.get_chat(int(admin_id))
                check('Admin Access', True, f"ID: {admin_id}")
            except Exception as e:
                check('Admin Access', False, str(e), critical=False)
    except Exception as e:
        check('Telegram', False, str(e))
        all_good = False
    
    # 5. SOLANA CONNECTION
    print(f"\n{bcolors.HEADER}⛓️ SOLANA CONNECTION{bcolors.ENDC}")
    try:
        from solana.rpc.async_api import AsyncClient
        client = AsyncClient(os.getenv('RPC_URL'))
        health = await client.get_health()
        check('RPC Health', True, str(health.value))
        
        # Balance check
        try:
            from solders.keypair import Keypair
            key = os.getenv('SOL_MAIN')
            wallet = Keypair.from_base58_string(key)
            balance = await client.get_balance(wallet.pubkey())
            sol = balance.value / 1e9
            check('Wallet Balance', sol > 0, f"{sol:.4f} SOL", critical=False)
        except Exception as e:
            check('Wallet', False, f"Solders error: {e}", critical=False)
            
        await client.close()
    except ImportError:
        check('Solana', False, "Package not installed")
        all_good = False
    except Exception as e:
        check('Solana RPC', False, str(e))
        all_good = False
    
    # 6. DATABASE
    print(f"\n{bcolors.HEADER}🗄️ DATABASE{bcolors.ENDC}")
    try:
        import asyncpg
        conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
        version = await conn.fetchval("SELECT version()")
        check('PostgreSQL', True, version[:30])
        await conn.close()
    except Exception as e:
        check('Database', False, str(e))
        all_good = False
    
    # 7. RUGCHECK API
    print(f"\n{bcolors.HEADER}🛡️ RUGCHECK API{bcolors.ENDC}")
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {os.getenv('RUGCHECK_API_KEY')}"}
            # Test with BONK
            async with session.get(
                "https://api.rugcheck.xyz/v2/tokens/DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263/report/summary",
                headers=headers
            ) as resp:
                if resp.status == 200:
                    check('RugCheck v2', True, "API responding")
                else:
                    check('RugCheck', False, f"Status {resp.status}", critical=False)
    except Exception as e:
        check('RugCheck', False, str(e), critical=False)
    
    # 8. GITHUB STATUS
    print(f"\n{bcolors.HEADER}📤 GITHUB STATUS{bcolors.ENDC}")
    try:
        result = subprocess.run(['git', 'status', '--short'], 
                              capture_output=True, text=True)
        if result.stdout.strip():
            check('Uncommitted', False, f"{len(result.stdout.strip().split(chr(10)))} files", critical=False)
        else:
            check('Git Clean', True, "Ready to push")
        
        # Check remote
        result = subprocess.run(['git', 'remote', '-v'], 
                              capture_output=True, text=True)
        if 'github.com' in result.stdout:
            check('Remote', True, "GitHub connected")
        else:
            check('Remote', False, "No GitHub remote")
    except Exception as e:
        check('Git', False, str(e), critical=False)
    
    # FINAL SUMMARY
    print(f"\n{bcolors.BOLD}{'='*60}")
    if all_good:
        print(f"{bcolors.OKGREEN}🚀 SYSTEM READY FOR DEPLOYMENT!{bcolors.ENDC}")
        print(f"\n{bcolors.OKCYAN}Next steps:")
        print("1. git push origin main")
        print("2. Go to render.com → New Web Service")
        print("3. Paste environment variables")
        print("4. Deploy!{bcolors.ENDC}")
    else:
        print(f"{bcolors.FAIL}❌ FIX CRITICAL ERRORS BEFORE DEPLOY{bcolors.ENDC}")
        print(f"\n{bcolors.WARNING}Priority fixes:")
        print("• Install missing packages: pip install solana solders")
        print("• Set missing env vars in .env file")
        print("• Fix Telegram token if invalid{bcolors.ENDC}")
    
    print(f"{'='*60}{bcolors.ENDC}\n")
    
    return all_good

if __name__ == "__main__":
    result = asyncio.run(run_checks())
    sys.exit(0 if result else 1)
