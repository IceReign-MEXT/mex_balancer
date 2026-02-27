"""Solana sniper engine"""
import asyncio
import base64
from typing import Dict, Optional
from solana.rpc.async_api import AsyncClient
from solana.transaction import Transaction
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.instruction import Instruction
from solders.compute_budget import set_compute_unit_price
from loguru import logger

class SolanaSniper:
    def __init__(self, rpc_url: str, wallet_key: str, encryption_key: str):
        self.client = AsyncClient(rpc_url, commitment="processed")
        self.wallet = Keypair.from_base58_string(wallet_key)
        self.wallet_address = str(self.wallet.pubkey())
        
    async def get_wallet_balance(self) -> float:
        """Get SOL balance"""
        try:
            response = await self.client.get_balance(self.wallet.pubkey())
            lamports = response.value
            return lamports / 1e9  # Convert to SOL
        except Exception as e:
            logger.error(f"Balance check failed: {e}")
            return 0.0
    
    async def snipe_token(self, token_address: str, amount_sol: float, 
                         slippage_bps: int, user_id: int) -> Dict:
        """
        Execute snipe with Jupiter/Raydium integration
        """
        try:
            # Get quote from Jupiter
            quote = await self._get_jupiter_quote(
                input_mint="So11111111111111111111111111111111111111112",  # SOL
                output_mint=token_address,
                amount=int(amount_sol * 1e9),
                slippage_bps=slippage_bps
            )
            
            if not quote:
                return {'success': False, 'error': 'No route found'}
            
            # Get swap transaction
            swap_tx = await self._get_jupiter_swap(quote)
            if not swap_tx:
                return {'success': False, 'error': 'Swap construction failed'}
            
            # Add priority fee for fast execution
            priority_fee = 10000  # 0.00001 SOL
            modified_tx = self._add_priority_fee(swap_tx, priority_fee)
            
            # Sign and send
            result = await self._send_transaction(modified_tx)
            
            if result['success']:
                return {
                    'success': True,
                    'signature': result['signature'],
                    'entry_price': quote.get('price', 0),
                    'token_amount': quote.get('outAmount', 0) / 1e6  # Assuming 6 decimals
                }
            else:
                return {'success': False, 'error': result['error']}
                
        except Exception as e:
            logger.error(f"Snipe failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _get_jupiter_quote(self, input_mint: str, output_mint: str, 
                                 amount: int, slippage_bps: int) -> Optional[Dict]:
        """Get quote from Jupiter API"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                url = f"https://quote-api.jup.ag/v6/quote?inputMint={input_mint}&outputMint={output_mint}&amount={amount}&slippageBps={slippage_bps}"
                async with session.get(url) as resp:
                    if resp.status == 200:
                        return await resp.json()
        except Exception as e:
            logger.error(f"Jupiter quote error: {e}")
        return None
    
    async def _get_jupiter_swap(self, quote: Dict) -> Optional[Transaction]:
        """Get swap transaction from Jupiter"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://quote-api.jup.ag/v6/swap",
                    json={
                        "quoteResponse": quote,
                        "userPublicKey": self.wallet_address,
                        "wrapAndUnwrapSol": True
                    }
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        tx_data = base64.b64decode(data['swapTransaction'])
                        return Transaction.deserialize(tx_data)
        except Exception as e:
            logger.error(f"Jupiter swap error: {e}")
        return None
    
    def _add_priority_fee(self, tx: Transaction, fee: int) -> Transaction:
        """Add priority fee instruction"""
        # Add compute budget instruction
        tx.add(set_compute_unit_price(fee))
        return tx
    
    async def _send_transaction(self, tx: Transaction) -> Dict:
        """Send with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Get fresh blockhash
                blockhash = await self.client.get_latest_blockhash()
                
                # Sign
                tx.sign(self.wallet, blockhash.value.blockhash)
                
                # Send with skip preflight for speed
                result = await self.client.send_transaction(
                    tx,
                    opts={"skip_preflight": True, "max_retries": 1}
                )
                
                # Wait for confirmation
                await asyncio.sleep(2)
                status = await self.client.get_signature_statuses([result.value])
                
                if status.value[0] and status.value[0].confirmation_status:
                    return {
                        'success': True,
                        'signature': str(result.value),
                        'status': str(status.value[0].confirmation_status)
                    }
                    
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(1)
        
        return {'success': False, 'error': 'Max retries exceeded'}
    
    async def get_token_value(self, token_address: str, amount: float) -> float:
        """Get current value of token holdings in SOL"""
        try:
            quote = await self._get_jupiter_quote(
                input_mint=token_address,
                output_mint="So11111111111111111111111111111111111111112",
                amount=int(amount * 1e6),
                slippage_bps=100
            )
            if quote:
                return quote.get('outAmount', 0) / 1e9
        except Exception as e:
            logger.error(f"Value check error: {e}")
        return 0.0
