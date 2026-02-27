"""Configuration management"""
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    # Telegram
    bot_token: str = os.getenv("BOT_TOKEN", "")
    admin_id: int = int(os.getenv("ADMIN_ID", "0"))
    channel_id: str = os.getenv("CHANNEL_ID", "")
    
    # RPC & APIs
    rpc_url: str = os.getenv("RPC_URL", "")
    helius_api_key: str = os.getenv("RPC_URL", "").split("api-key=")[-1] if "api-key=" in os.getenv("RPC_URL", "") else ""
    rugcheck_api_key: str = os.getenv("RUGCHECK_API_KEY", "")
    
    # Security
    sol_main: str = os.getenv("SOL_MAIN", "")
    encryption_key: str = os.getenv("ENCRYPTION_KEY", "")
    fee_wallet: str = os.getenv("FEE_WALLET", "") or os.getenv("SOL_MAIN", "")
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", "")
    
    # Trading
    min_trade_amount: float = 0.01
    max_slippage: float = 0.05
    default_profit_target: float = 2.0
    default_stop_loss: float = 0.8
    
    def validate(self):
        required = [self.bot_token, self.rpc_url, self.sol_main, self.database_url]
        if not all(required):
            raise ValueError("Missing required environment variables")
