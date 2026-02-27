import aiohttp, os

class TradingEngine:
    def __init__(self):
        self.jup_api = "https://quote-api.jup.ag/v6"

    async def get_swap_quote(self, input_mint, output_mint, amount_sol):
        # Convert SOL to Lamports (10^9)
        lamports = int(amount_sol * 10**9)
        url = f"{self.jup_api}/quote?inputMint={input_mint}&outputMint={output_mint}&amount={lamports}&slippageBps=1500"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                return await resp.json()

engine = TradingEngine()
