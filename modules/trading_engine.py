import aiohttp, os, json

class TradingEngine:
    def __init__(self):
        self.jup_quote_url = "https://quote-api.jup.ag/v6/quote"
        self.jup_swap_url = "https://quote-api.jup.ag/v6/swap"

    async def get_quote(self, token_address, amount_sol):
        # Convert SOL to lamports
        lamports = int(amount_sol * 10**9)
        params = {
            "inputMint": "So11111111111111111111111111111111111111112",
            "outputMint": token_address,
            "amount": str(lamports),
            "slippageBps": "1500" # 15% slippage
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(self.jup_quote_url, params=params) as resp:
                return await resp.json()

    async def get_swap_tx(self, quote_response, user_pubkey):
        payload = {
            "quoteResponse": quote_response,
            "userPublicKey": user_pubkey,
            "wrapAndUnwrapSol": True,
            "prioritizationFeeLamports": 100000 # "Turbo" fee
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(self.jup_swap_url, json=payload) as resp:
                data = await resp.json()
                return data.get("swapTransaction")

engine = TradingEngine()
