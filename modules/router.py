import os
from modules.trading_engine import TokenAnalyzer

class GuardianRouter:
    def __init__(self):
        self.safe_wallet = os.getenv("SOL_MAIN")
        self.analyzer = TokenAnalyzer()

    async def secure_snipe(self, mint):
        analysis = await self.analyzer.full_analysis(mint)
        if not analysis["is_safe"]: return "🛡️ **SHIELD:** Potential Rug. Blocked."
        return f"🚀 **SUCCESS:** Snipe routed to {self.safe_wallet[:6]}..."

router = GuardianRouter()
