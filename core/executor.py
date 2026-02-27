import os, json, aiohttp
from core.security import security

class SniperExecutor:
    def __init__(self):
        self.rpc_url = os.getenv("RPC_URL")
        self.vault_path = "core/.secret_vault"

    async def get_balance(self):
        if not os.path.exists(self.vault_path): return 0
        with open(self.vault_path, "r") as f:
            pub_key = f.read().split(":")[0]
        
        payload = {"jsonrpc": "2.0", "id": 1, "method": "getBalance", "params": [pub_key]}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.rpc_url, json=payload) as resp:
                    res = await resp.json()
                    return res.get("result", {}).get("value", 0) / 10**9
        except:
            return 0

executor = SniperExecutor()
