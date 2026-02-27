import os
from core.scanner import scanner
from modules.trading_engine import engine

class Router:
    async def secure_snipe(self, token_address):
        # 1. SCAN
        is_safe, scan_msg = scanner.check_token(token_address)
        if not is_safe:
            return scan_msg

        # 2. QUOTE (Testing with 0.04 SOL ~ $5-6)
        quote = await engine.get_quote(token_address, 0.04)
        if "outAmount" not in quote:
            return f"{scan_msg}\n\n❌ **LIQUIDITY ERROR:** Jupiter cannot find a trade route."

        # 3. PREPARE
        # We don't execute yet—we show the user the "Weapon is Armed"
        out_amount = int(quote['outAmount']) / 10**6 # Approximate for 6-decimal tokens
        return (f"{scan_msg}\n\n🎯 **TARGET LOCKED**\n"
                f"Action: Buy $5 SOL -> Token\n"
                f"Est. Output: {out_amount:,.2f} tokens\n"
                f"Slippage: 15%\n\n*Execute with /confirm [CA]*")

router = Router()
