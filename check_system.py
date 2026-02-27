#!/usr/bin/env python3
"""
🔍 MEX BALANCER - COMPLETE SYSTEM CHECKER
Verifies all files, env vars, connections, and bot readiness
"""

import os
import sys
import asyncio
import importlib.util
from pathlib import Path
from datetime import datetime

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{text.center(60)}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.END}")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")

class SystemChecker:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.success = []
        
    def check_file_structure(self):
        """Verify all required files exist"""
        print_header("📁 FILE STRUCTURE CHECK")
        
        required_files = {
            'main.py': 'Main bot entry point',
            'requirements.txt': 'Python dependencies',
            'Procfile': 'Render deployment config',
            'runtime.txt': 'Python version',
            'health_server.py': 'Health check server',
            'deploy.sh': 'Deployment script',
            '.env': 'Environment variables (CRITICAL)',
            'core/config.py': 'Configuration module',
            'core/security.py': 'Security module',
            'core/database.py': 'Database module',
            'core/sniper.py': 'Trading engine',
            'core/analyzer.py': 'Token analyzer',
            'core/auto_trader.py': 'Auto-trading logic',
            'core/monetization.py': 'Fee management',
            'core/__init__.py': 'Core package marker',
            'logs/': 'Log directory'
        }
        
        for file, description in required_files.items():
            path = Path(file)
            if path.exists():
                size = path.stat().st_size if path.is_file() else '-'
                print_success(f"{file:<30} ({description})")
                self.success.append(f"File exists: {file}")
            else:
                print_error(f"{file:<30} MISSING - {description}")
                self.errors.append(f"Missing file: {file}")
        
        return len(self.errors) == 0

    def check_environment_variables(self):
        """Verify all env vars are set"""
        print_header("🔐 ENVIRONMENT VARIABLES CHECK")
        
        required_vars = {
            'BOT_TOKEN': 'Telegram bot authentication',
            'ADMIN_ID': 'Admin user ID',
            'CHANNEL_ID': 'Telegram channel ID',
            'RPC_URL': 'Helius RPC endpoint',
            'RUGCHECK_API_KEY': 'RugCheck API access',
            'SOL_MAIN': 'Trading wallet private key',
            'ENCRYPTION_KEY': 'Data encryption key',
            'DATABASE_URL': 'Supabase PostgreSQL URL'
        }
        
        env_file_path = Path('.env')
        env_vars = {}
        
        # Load from .env file if exists
        if env_file_path.exists():
            with open(env_file_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key] = value
                        os.environ[key] = value
        
        for var, description in required_vars.items():
            value = env_vars.get(var) or os.getenv(var)
            
            if value:
                # Mask sensitive values
                if 'KEY' in var or 'TOKEN' in var or 'MAIN' in var or 'URL' in var:
                    if len(value) > 20:
                        masked = value[:10] + '...' + value[-5:]
                    else:
                        masked = '***'
                    print_success(f"{var:<20} = {masked} ({description})")
                else:
                    print_success(f"{var:<20} = {value} ({description})")
                self.success.append(f"Env var set: {var}")
            else:
                print_error(f"{var:<20} MISSING - {description}")
                self.errors.append(f"Missing env var: {var}")
        
        return len(self.errors) == 0

    def check_python_dependencies(self):
        """Verify all packages are installed"""
        print_header("📦 PYTHON DEPENDENCIES CHECK")
        
        required_packages = [
            'solana', 'solders', 'anchorpy', 'telegram',
            'asyncpg', 'cryptography', 'aiohttp', 'loguru',
            'websockets', 'python-dotenv', 'mnemonic'
        ]
        
        missing = []
        for package in required_packages:
            try:
                # Handle special cases
                import_name = package.replace('-', '_')
                if package == 'telegram':
                    import_name = 'telegram.ext'
                
                spec = importlib.util.find_spec(import_name.split('.')[0])
                if spec is None:
                    missing.append(package)
                    print_error(f"{package:<20} NOT INSTALLED")
                else:
                    print_success(f"{package:<20} INSTALLED")
                    self.success.append(f"Package installed: {package}")
            except Exception as e:
                missing.append(package)
                print_error(f"{package:<20} ERROR: {e}")
        
        if missing:
            self.errors.append(f"Missing packages: {', '.join(missing)}")
            print_warning("\nInstall missing packages with:")
            print_warning("pip install " + " ".join(missing))
        
        return len(missing) == 0

    async def check_telegram_connection(self):
        """Test Telegram bot connectivity"""
        print_header("📱 TELEGRAM CONNECTION CHECK")
        
        try:
            from telegram import Bot
            token = os.getenv('BOT_TOKEN')
            
            if not token:
                print_error("BOT_TOKEN not set - cannot test")
                return False
            
            bot = Bot(token=token)
            me = await bot.get_me()
            
            print_success(f"Bot connected: @{me.username}")
            print_success(f"Bot ID: {me.id}")
            print_success(f"Bot Name: {me.first_name}")
            
            # Test admin ID
            admin_id = os.getenv('ADMIN_ID')
            if admin_id:
                try:
                    chat = await bot.get_chat(int(admin_id))
                    print_success(f"Admin access verified: {chat.username or chat.first_name}")
                except Exception as e:
                    print_warning(f"Admin check failed: {e}")
                    print_warning("Make sure you /start the bot first")
            
            # Test channel
            channel_id = os.getenv('CHANNEL_ID')
            if channel_id:
                try:
                    chat = await bot.get_chat(channel_id)
                    print_success(f"Channel access verified: {chat.title}")
                except Exception as e:
                    print_warning(f"Channel check failed: {e}")
                    print_warning("Add bot as admin to channel first")
            
            self.success.append("Telegram connection OK")
            return True
            
        except Exception as e:
            print_error(f"Telegram connection failed: {e}")
            self.errors.append(f"Telegram error: {e}")
            return False

    async def check_solana_connection(self):
        """Test Solana RPC connection"""
        print_header("⛓️ SOLANA CONNECTION CHECK")
        
        try:
            from solana.rpc.async_api import AsyncClient
            
            rpc_url = os.getenv('RPC_URL')
            if not rpc_url:
                print_error("RPC_URL not set")
                return False
            
            # Hide API key in logs
            display_url = rpc_url.split('?')[0] if '?' in rpc_url else rpc_url
            print_info(f"Connecting to: {display_url}...")
            
            client = AsyncClient(rpc_url)
            
            # Get latest blockhash (fast test)
            response = await client.get_latest_blockhash()
            
            if response.value:
                print_success(f"RPC connection: OK")
                print_success(f"Blockhash: {str(response.value.blockhash)[:20]}...")
                print_success(f"Slot: {response.context.slot}")
                
                # Get wallet balance if key exists
                wallet_key = os.getenv('SOL_MAIN')
                if wallet_key:
                    try:
                        from solders.keypair import Keypair
                        wallet = Keypair.from_base58_string(wallet_key)
                        balance = await client.get_balance(wallet.pubkey())
                        sol_balance = balance.value / 1e9
                        
                        if sol_balance > 0:
                            print_success(f"Wallet balance: {sol_balance:.4f} SOL")
                            if sol_balance < 0.05:
                                print_warning("Balance low! Deposit more SOL")
                        else:
                            print_warning("Wallet empty - deposit SOL to start trading")
                            
                    except Exception as e:
                        print_warning(f"Wallet check failed: {e}")
                
                self.success.append("Solana RPC OK")
                await client.close()
                return True
            else:
                print_error("RPC returned empty response")
                return False
                
        except Exception as e:
            print_error(f"Solana connection failed: {e}")
            self.errors.append(f"Solana RPC error: {e}")
            return False

    async def check_database_connection(self):
        """Test Supabase PostgreSQL"""
        print_header("🗄️ DATABASE CONNECTION CHECK")
        
        try:
            import asyncpg
            
            db_url = os.getenv('DATABASE_URL')
            if not db_url:
                print_error("DATABASE_URL not set")
                return False
            
            # Mask credentials
            masked = db_url.replace(db_url.split(':')[2].split('@')[0], '***')
            print_info(f"Connecting to database...")
            
            conn = await asyncpg.connect(db_url)
            version = await conn.fetchval("SELECT version()")
            
            print_success("Database connection: OK")
            print_success(f"PostgreSQL: {version[:30]}...")
            
            # Test table creation
            try:
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS test_connection (
                        id SERIAL PRIMARY KEY,
                        test_time TIMESTAMP DEFAULT NOW()
                    )
                """)
                print_success("Table creation: OK")
                
                # Cleanup
                await conn.execute("DROP TABLE IF EXISTS test_connection")
                
            except Exception as e:
                print_warning(f"Table test warning: {e}")
            
            await conn.close()
            self.success.append("Database OK")
            return True
            
        except Exception as e:
            print_error(f"Database connection failed: {e}")
            self.errors.append(f"Database error: {e}")
            return False

    async def check_rugcheck_api(self):
        """Test RugCheck API"""
        print_header("🛡️ RUGCHECK API CHECK")
        
        try:
            import aiohttp
            
            api_key = os.getenv('RUGCHECK_API_KEY')
            if not api_key:
                print_error("RUGCHECK_API_KEY not set")
                return False
            
            # Test with a known safe token (USDC)
            test_token = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
            
            headers = {"Authorization": f"Bearer {api_key}"}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://api.rugcheck.xyz/v1/tokens/verify/solana/{test_token}",
                    headers=headers
                ) as resp:
                    
                    if resp.status == 200:
                        data = await resp.json()
                        score = data.get('score', 'N/A')
                        print_success(f"RugCheck API: OK")
                        print_success(f"Test token score: {score}/100")
                        self.success.append("RugCheck API OK")
                        return True
                    elif resp.status == 401:
                        print_error("Invalid API key")
                        return False
                    else:
                        print_warning(f"API returned status {resp.status}")
                        return False
                        
        except Exception as e:
            print_error(f"RugCheck test failed: {e}")
            self.errors.append(f"RugCheck error: {e}")
            return False

    def check_security(self):
        """Security validation"""
        print_header("🔒 SECURITY CHECK")
        
        issues = []
        
        # Check .env is in .gitignore
        gitignore = Path('.gitignore')
        if gitignore.exists():
            content = gitignore.read_text()
            if '.env' in content:
                print_success(".env is in .gitignore")
            else:
                print_error(".env NOT in .gitignore - CRITICAL!")
                issues.append("Add .env to .gitignore")
        else:
            print_warning("No .gitignore file")
            issues.append("Create .gitignore")
        
        # Check wallet key format
        wallet_key = os.getenv('SOL_MAIN', '')
        if len(wallet_key) < 80:
            print_error("SOL_MAIN looks invalid (too short)")
            issues.append("Check SOL_MAIN format")
        else:
            print_success("SOL_MAIN format looks valid")
        
        # Check encryption key
        enc_key = os.getenv('ENCRYPTION_KEY', '')
        if len(enc_key) < 20:
            print_warning("ENCRYPTION_KEY might be weak")
        else:
            print_success("ENCRYPTION_KEY present")
        
        if issues:
            self.warnings.extend(issues)
            return False
        return True

    def print_final_report(self):
        """Print summary"""
        print_header("📊 FINAL REPORT")
        
        print(f"\n{Colors.GREEN}{Colors.BOLD}SUCCESS ({len(self.success)}):{Colors.END}")
        for item in self.success[-10:]:  # Last 10
            print(f"  ✅ {item}")
        
        if self.warnings:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}WARNINGS ({len(self.warnings)}):{Colors.END}")
            for item in self.warnings:
                print(f"  ⚠️  {item}")
        
        if self.errors:
            print(f"\n{Colors.RED}{Colors.BOLD}ERRORS ({len(self.errors)}):{Colors.END}")
            for item in self.errors:
                print(f"  ❌ {item}")
        
        print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
        
        if not self.errors:
            print(f"{Colors.GREEN}{Colors.BOLD}🚀 SYSTEM READY FOR DEPLOYMENT!{Colors.END}")
            print(f"\n{Colors.BOLD}Next steps:{Colors.END}")
            print("1. git push origin main")
            print("2. Go to render.com and create web service")
            print("3. Add environment variables")
            print("4. Deploy!")
            return True
        else:
            print(f"{Colors.RED}{Colors.BOLD}❌ FIX ERRORS BEFORE DEPLOYMENT{Colors.END}")
            print(f"\n{Colors.BOLD}Priority fixes:{Colors.END}")
            print("1. Install missing dependencies: pip install -r requirements.txt")
            print("2. Set missing environment variables in .env")
            print("3. Run check again: python check_system.py")
            return False

async def main():
    print(f"{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{'MEX BALANCER - SYSTEM CHECKER':^60}{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    checker = SystemChecker()
    
    # Run all checks
    checker.check_file_structure()
    checker.check_environment_variables()
    checker.check_python_dependencies()
    checker.check_security()
    
    # Async checks
    await checker.check_telegram_connection()
    await checker.check_solana_connection()
    await checker.check_database_connection()
    await checker.check_rugcheck_api()
    
    # Final report
    ready = checker.print_final_report()
    
    sys.exit(0 if ready else 1)

if __name__ == "__main__":
    asyncio.run(main())
