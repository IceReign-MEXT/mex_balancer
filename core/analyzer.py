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
            # Try RugCheck v2 API
            rugcheck_data = await self._rugcheck_scan(token_address)
            if rugcheck_data:
                result['risk_score'] = rugcheck_data.get('score', 100)
                result['is_safe'] = result['risk_score'] < 50
                
                token_data = rugcheck_data.get('token', {})
                result['mint_authority'] = token_data.get('mintAuthority') is not None
                result['freeze_authority'] = token_data.get('freezeAuthority') is not None
                
                risks = rugcheck_data.get('risks', [])
                if risks:
                    result['danger_reason'] = risks[0].get('description', 'Unknown risk')
                
                markets = rugcheck_data.get('markets', [])
                if markets:
                    liq = sum(m.get('liquidityA', 0) + m.get('liquidityB', 0) for m in markets)
                    result['liquidity_usd'] = liq
                
                file_meta = rugcheck_data.get('fileMeta', {})
                result['holder_count'] = file_meta.get('holder', 0)
                
                top_holders = rugcheck_data.get('topHolders', [])
                if top_holders:
                    result['top10_percentage'] = sum(h.get('pct', 0) for h in top_holders[:10])
            
            # Calculate safety
            result['safety_score'] = max(0, 100 - result['risk_score'])
            
            # Critical overrides
            if result['risk_score'] > 70:
                result['is_safe'] = False
                result['danger_reason'] = result['danger_reason'] or "High risk score"
            
            if result['top10_percentage'] > 50:
                result['is_safe'] = False
                result['danger_reason'] = "Whale concentration >50%"
            
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            result['danger_reason'] = f"Analysis failed: {str(e)}"
        
        return result
    
    async def _rugcheck_scan(self, token: str) -> Dict:
        """Scan with RugCheck v2 API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.rugcheck_key}",
                "Content-Type": "application/json"
            }
            
            # Try multiple endpoints
            endpoints = [
                f"https://api.rugcheck.xyz/v2/tokens/{token}/report/summary",
                f"https://api.rugcheck.xyz/v1/tokens/verify/solana/{token}",
            ]
            
            for url in endpoints:
                try:
                    async with self.session.get(url, headers=headers) as resp:
                        if resp.status == 200:
                            return await resp.json()
                        elif resp.status == 404:
                            continue  # Try next endpoint
                except:
                    continue
            
            logger.warning(f"All RugCheck endpoints failed for {token}")
            return {}
                    
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
