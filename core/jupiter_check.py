"""Fallback safety check using Jupiter"""
import aiohttp

async def check_token_safety(token: str):
    """Check if token is tradable on Jupiter"""
    try:
        async with aiohttp.ClientSession() as session:
            # Get token info from Jupiter
            async with session.get(
                f"https://token.jup.ag/all"
            ) as resp:
                if resp.status == 200:
                    tokens = await resp.json()
                    token_info = next((t for t in tokens if t.get('address') == token), None)
                    
                    if token_info:
                        return {
                            'is_safe': True,
                            'risk_score': 50,  # Neutral without full check
                            'liquidity_usd': token_info.get('dailyVolume', 0),
                            'source': 'jupiter'
                        }
                    else:
                        return {
                            'is_safe': False,
                            'risk_score': 100,
                            'danger_reason': 'Token not found on Jupiter',
                            'source': 'jupiter'
                        }
    except Exception as e:
        return {'is_safe': False, 'error': str(e)}
    
    return {'is_safe': False, 'error': 'Check failed'}
