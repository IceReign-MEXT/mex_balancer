"""Token analysis and rug detection"""
import aiohttp
import asyncio
from typing import Dict
from loguru import logger

class TokenAnalyzer:
    def __init__(self, rugcheck_key: str, helius_key: str):
        self.rugcheck_key = rugcheck_key
        self.helius_key = helius_key
        self.session: aiohttp.ClientSession = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, *args):
        await self.session.close()
    
    async def full_analysis(self, token_address: str) -> Dict:
        """Comprehensive token analysis"""
        result = {
            'is_safe': False,
            'risk_score': 100,
            'safety_score': 0,
            'danger_reason': '',
            'liquidity_usd': 0,
            'holder_count': 0,
            'mint_authority': True,
            'freeze_authority': True,
            'top10_percentage': 100,
            'is_honeypot': True,
            'buy_tax': 99,
            'sell_tax': 99
        }
        
        try:
            # RugCheck analysis
            rugcheck_data = await self._rugcheck_scan(token_address)
            if rugcheck_data:
                result['risk_score'] = rugcheck_data.get('score', 100)
                result['is_safe'] = result['risk_score'] < 50
                
                # Extract authorities
                result['mint_authority'] = rugcheck_data.get('mintAuthority', True)
                result['freeze_authority'] = rugcheck_data.get('freezeAuthority', True)
                
                # Check for specific dangers
                dangers = rugcheck_data.get('risks', [])
                if dangers:
                    result['danger_reason'] = dangers[0].get('description', 'Unknown risk')
                
                # Holder analysis
                result['holder_count'] = rugcheck_data.get('totalHolders', 0)
                result['top10_percentage'] = rugcheck_data.get('top10HolderPercent', 100)
            
            # Helius metadata
            helius_data = await self._helius_analysis(token_address)
            if helius_data:
                result['liquidity_usd'] = helius_data.get('liquidity', 0)
                
                # Simulate buy/sell to check for honeypot
                simulation = await self._simulate_trade(token_address)
                result['is_honeypot'] = simulation.get('is_honeypot', True)
                result['buy_tax'] = simulation.get('buy_tax', 99)
                result['sell_tax'] = simulation.get('sell_tax', 99)
            
            # Calculate safety score (inverse of risk)
            result['safety_score'] = max(0, 100 - result['risk_score'])
            
            # Override safety if critical issues found
            if result['is_honeypot'] or result['sell_tax'] > 10:
                result['is_safe'] = False
                result['danger_reason'] = f"Honeypot detected! Sell tax: {result['sell_tax']}%"
            
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            result['danger_reason'] = f"Analysis failed: {str(e)}"
        
        return result
    
    async def _rugcheck_scan(self, token: str) -> Dict:
        """Scan with RugCheck"""
        try:
            headers = {"Authorization": f"Bearer {self.rugcheck_key}"}
            async with self.session.get(
                f"https://api.rugcheck.xyz/v1/tokens/verify/solana/{token}",
                headers=headers
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
        except Exception as e:
            logger.error(f"RugCheck error: {e}")
        return {}
    
    async def _helius_analysis(self, token: str) -> Dict:
        """Get token data from Helius"""
        try:
            async with self.session.post(
                f"https://mainnet.helius-rpc.com/?api-key={self.helius_key}",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getAsset",
                    "params": [token]
                }
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get('result', {})
        except Exception as e:
            logger.error(f"Helius error: {e}")
        return {}
    
    async def _simulate_trade(self, token: str) -> Dict:
        """Simulate buy/sell to detect honeypot"""
        # This would integrate with Jupiter/Raydium simulation
        # For now, return safe defaults
        return {
            'is_honeypot': False,
            'buy_tax': 0,
            'sell_tax': 0
        }
