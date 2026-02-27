from core.scanner import scanner
from modules.trading_engine import engine

class Router:
    async def secure_snipe(self, token_address):
        # 1. Scan for Rugs
        is_safe, message = scanner.check_token(token_address)
        if not is_safe:
            return message
        
        # 2. If safe, get a quote for a $5 buy (half of your $10)
        quote = await engine.get_swap_quote(
            "So11111111111111111111111111111111111111112", # SOL
            token_address,
            0.04 # approx $5-6
        )
        
        if "outAmount" in quote:
            return f"🎯 **TARGET ACQUIRED**\n{message}\n\nEstimated Output: {quote['outAmount']}\nRoute: Jupiter Aggregator\n\n*Execute transaction? (Feature coming in next update)*"
        return f"❌ Quote Error: Could not find liquidity for this token."

router = Router()
