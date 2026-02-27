"""Database operations"""
import asyncpg
from datetime import datetime
from typing import Optional, List, Dict
from loguru import logger

class DatabaseManager:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self):
        """Create connection pool"""
        self.pool = await asyncpg.create_pool(self.database_url)
        await self._create_tables()
    
    async def _create_tables(self):
        """Initialize schema"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    token_address TEXT NOT NULL,
                    amount_sol NUMERIC(20, 9) NOT NULL,
                    entry_price NUMERIC(20, 9),
                    exit_price NUMERIC(20, 9),
                    token_amount NUMERIC(20, 9),
                    tx_signature TEXT UNIQUE,
                    status TEXT DEFAULT 'active',
                    fee_paid NUMERIC(20, 9) DEFAULT 0,
                    pnl_percent NUMERIC(10, 2),
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),
                    auto_sell_enabled BOOLEAN DEFAULT TRUE,
                    tp1_hit BOOLEAN DEFAULT FALSE,
                    tp2_hit BOOLEAN DEFAULT FALSE
                );
                
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username TEXT,
                    wallet_address TEXT,
                    total_trades INTEGER DEFAULT 0,
                    profitable_trades INTEGER DEFAULT 0,
                    total_pnl_sol NUMERIC(20, 9) DEFAULT 0,
                    created_at TIMESTAMP DEFAULT NOW()
                );
                
                CREATE INDEX IF NOT EXISTS idx_trades_user ON trades(user_id);
                CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status);
            """)
    
    async def record_trade(self, user_id: int, token: str, amount_sol: float,
                          entry_price: float, tx_signature: str, fee_paid: float) -> int:
        """Record new trade"""
        async with self.pool.acquire() as conn:
            trade_id = await conn.fetchval("""
                INSERT INTO trades (user_id, token_address, amount_sol, entry_price, 
                                  tx_signature, fee_paid)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
            """, user_id, token, amount_sol, entry_price, tx_signature, fee_paid)
            
            # Update user stats
            await conn.execute("""
                INSERT INTO users (user_id, total_trades)
                VALUES ($1, 1)
                ON CONFLICT (user_id) 
                DO UPDATE SET total_trades = users.total_trades + 1
            """, user_id)
            
            return trade_id
    
    async def get_active_positions(self, user_id: int) -> List[Dict]:
        """Get active trades"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM trades 
                WHERE user_id = $1 AND status = 'active'
                ORDER BY created_at DESC
            """, user_id)
            return [dict(row) for row in rows]
    
    async def update_trade_exit(self, trade_id: int, exit_price: float, 
                                pnl_percent: float, status: str = 'closed'):
        """Update trade on exit"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE trades 
                SET exit_price = $1, pnl_percent = $2, status = $3, updated_at = NOW()
                WHERE id = $4
            """, exit_price, pnl_percent, status, trade_id)
    
    async def close(self):
        """Close pool"""
        if self.pool:
            await self.pool.close()
