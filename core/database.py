"""Database operations using psycopg2"""
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import Optional, List, Dict
from loguru import logger

class DatabaseManager:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.conn = None
    
    def connect(self):
        """Create connection"""
        self.conn = psycopg2.connect(self.database_url, cursor_factory=RealDictCursor)
        self._create_tables()
    
    def _create_tables(self):
        """Initialize schema"""
        with self.conn.cursor() as cur:
            cur.execute("""
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
            self.conn.commit()
    
    def record_trade(self, user_id: int, token: str, amount_sol: float,
                    entry_price: float, tx_signature: str, fee_paid: float) -> int:
        """Record new trade"""
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO trades (user_id, token_address, amount_sol, entry_price, 
                                  tx_signature, fee_paid)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (user_id, token, amount_sol, entry_price, tx_signature, fee_paid))
            
            trade_id = cur.fetchone()['id']
            
            # Update user stats
            cur.execute("""
                INSERT INTO users (user_id, total_trades)
                VALUES (%s, 1)
                ON CONFLICT (user_id) 
                DO UPDATE SET total_trades = users.total_trades + 1
            """, (user_id,))
            
            self.conn.commit()
            return trade_id
    
    def get_active_positions(self, user_id: int) -> List[Dict]:
        """Get active trades"""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT * FROM trades 
                WHERE user_id = %s AND status = 'active'
                ORDER BY created_at DESC
            """, (user_id,))
            return [dict(row) for row in cur.fetchall()]
    
    def update_trade_exit(self, trade_id: int, exit_price: float, 
                         pnl_percent: float, status: str = 'closed'):
        """Update trade on exit"""
        with self.conn.cursor() as cur:
            cur.execute("""
                UPDATE trades 
                SET exit_price = %s, pnl_percent = %s, status = %s, updated_at = NOW()
                WHERE id = %s
            """, (exit_price, pnl_percent, status, trade_id))
            self.conn.commit()
    
    def update_trade_pnl(self, trade_id: int, pnl_percent: float):
        """Update current P&L"""
        with self.conn.cursor() as cur:
            cur.execute("""
                UPDATE trades SET pnl_percent = %s WHERE id = %s
            """, (pnl_percent, trade_id))
            self.conn.commit()
    
    def close(self):
        """Close connection"""
        if self.conn:
            self.conn.close()
