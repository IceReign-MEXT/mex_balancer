"""Database using HTTP requests to Supabase REST API"""
import requests
from datetime import datetime
from typing import List, Dict
from loguru import logger

class DatabaseManager:
    def __init__(self, database_url: str):
        # Parse Supabase URL for REST API
        self.database_url = database_url
        self.rest_url = None
        self.api_key = None
        
        # Extract from postgres URL format
        if 'supabase.com' in database_url:
            # Convert to REST API URL
            parts = database_url.replace('postgresql://', '').split('@')
            if len(parts) == 2:
                creds, host = parts
                user_pass = creds.split(':')
                if len(user_pass) >= 2:
                    self.api_key = user_pass[-1].split('@')[0] if '@' in user_pass[-1] else user_pass[-1]
                host_clean = host.split('/')[0].replace(':6543', '').replace(':5432', '')
                # Extract project ref
                if 'pooler.supabase.com' in host:
                    project_ref = host.split('.')[0]
                    self.rest_url = f"https://{project_ref}.supabase.co/rest/v1"
    
    def connect(self):
        """Test connection"""
        if self.rest_url:
            try:
                headers = {
                    "apikey": self.api_key,
                    "Authorization": f"Bearer {self.api_key}"
                }
                resp = requests.get(f"{self.rest_url}/trades?limit=1", headers=headers)
                logger.info(f"Supabase REST connected: {resp.status_code}")
            except Exception as e:
                logger.error(f"Database connection failed: {e}")
                # Use local SQLite fallback
                self._init_sqlite()
        else:
            self._init_sqlite()
    
    def _init_sqlite(self):
        """Fallback to SQLite"""
        import sqlite3
        self.sqlite_conn = sqlite3.connect('trades.db')
        self.sqlite_conn.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                token_address TEXT,
                amount_sol REAL,
                entry_price REAL,
                status TEXT DEFAULT 'active'
            )
        """)
        self.sqlite_conn.commit()
        logger.info("Using SQLite fallback")
    
    def record_trade(self, user_id: int, token: str, amount_sol: float,
                    entry_price: float, tx_signature: str, fee_paid: float) -> int:
        """Record trade"""
        if hasattr(self, 'sqlite_conn'):
            cur = self.sqlite_conn.cursor()
            cur.execute("""
                INSERT INTO trades (user_id, token_address, amount_sol, entry_price, tx_signature, fee_paid)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, token, amount_sol, entry_price, tx_signature, fee_paid))
            self.sqlite_conn.commit()
            return cur.lastrowid
        return 1
    
    def get_active_positions(self, user_id: int) -> List[Dict]:
        """Get active trades"""
        if hasattr(self, 'sqlite_conn'):
            cur = self.sqlite_conn.cursor()
            cur.execute("SELECT * FROM trades WHERE user_id=? AND status='active'", (user_id,))
            rows = cur.fetchall()
            return [{"id": r[0], "token_address": r[2], "amount_sol": r[3]} for r in rows]
        return []
    
    def update_trade_exit(self, trade_id: int, exit_price: float, pnl_percent: float, status: str = 'closed'):
        """Update trade"""
        if hasattr(self, 'sqlite_conn'):
            self.sqlite_conn.execute("""
                UPDATE trades SET exit_price=?, pnl_percent=?, status=? WHERE id=?
            """, (exit_price, pnl_percent, status, trade_id))
            self.sqlite_conn.commit()
    
    def close(self):
        if hasattr(self, 'sqlite_conn'):
            self.sqlite_conn.close()
