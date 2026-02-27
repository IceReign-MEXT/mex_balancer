import aiohttp
import asyncio
import os

async def test():
    api_key = os.getenv('RUGCHECK_API_KEY')
    # Test with BONK (known token)
    test_token = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"
    
    headers = {"Authorization": f"Bearer {api_key}"}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://api.rugcheck.xyz/v1/tokens/verify/solana/{test_token}",
            headers=headers
        ) as resp:
            print(f"Status: {resp.status}")
            if resp.status == 200:
                data = await resp.json()
                print(f"Score: {data.get('score')}")
                print("✅ RugCheck working!")
            else:
                text = await resp.text()
                print(f"Response: {text[:200]}")

asyncio.run(test())
