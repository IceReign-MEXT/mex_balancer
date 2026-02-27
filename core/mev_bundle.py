"""
⚡ MEV BUNDLE SUBMISSION
Submit transactions to Jito block engine for faster execution
"""

import aiohttp
import base64
from typing import Dict, List
from loguru import logger

class MEVBundler:
    """Submit transactions via Jito for MEV protection"""
    
    def __init__(self, jito_api_key: str = ""):
        self.jito_endpoint = "https://mainnet.block-engine.jito.wtf/api/v1"
        self.api_key = jito_api_key
        self.bundle_id = 0
    
    async def submit_bundle(self, transactions: List[str], tip_lamports: int = 10000) -> Dict:
        """
        Submit transaction bundle to Jito
        transactions: List of base58 encoded transactions
        """
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": self.bundle_id,
                "method": "sendBundle",
                "params": [
                    transactions,
                    {
                        "tip": tip_lamports,
                        "api_key": self.api_key
                    }
                ]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.jito_endpoint}/bundles",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as resp:
                    
                    if resp.status == 200:
                        result = await resp.json()
                        self.bundle_id += 1
                        return {
                            "success": True,
                            "bundle_id": result.get("result"),
                            "tip": tip_lamports
                        }
                    else:
                        return {"success": False, "error": f"HTTP {resp.status}"}
                        
        except Exception as e:
            logger.error(f"MEV bundle error: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_bundle_status(self, bundle_id: str) -> Dict:
        """Check if bundle was included in block"""
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getBundleStatuses",
                "params": [[bundle_id]]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.jito_endpoint}/bundles",
                    json=payload
                ) as resp:
                    
                    if resp.status == 200:
                        result = await resp.json()
                        return {
                            "success": True,
                            "status": result.get("result", {}).get("value", [{}])[0]
                        }
                    else:
                        return {"success": False, "error": f"HTTP {resp.status}"}
                        
        except Exception as e:
            return {"success": False, "error": str(e)}

