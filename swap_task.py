from typing import Any, Dict
from loguru import logger

from tasks.base_task import BaseTask
from core.web3_wrapper import Web3Wrapper
from utils.helpers import retry, async_random_delay
from utils.transaction_tracker import TransactionTracker


class SwapTask(BaseTask):
    """Task for performing token swaps on a Decentralized Exchange (DEX)."""

    def __init__(self, private_key: str, rpc_url: str, account_address: str, proxy: str = None, task_id: str = None) -> None:
        super().__init__(private_key, rpc_url, account_address, proxy, task_id)
        self.web3_client = Web3Wrapper(private_key=private_key, rpc_url=rpc_url)
        self.tracker = TransactionTracker()

    @retry(attempts=3, delay=10, backoff=1.5)
    async def execute(self, token_in_address: str, token_out_address: str, amount_in: int) -> Dict[str, Any]:
        """Executes the token swap with transaction tracking.

        Args:
            token_in_address: The address of the input token.
            token_out_address: The address of the output token.
            amount_in: The amount of input tokens (in smallest unit).

        Returns:
            A dictionary containing the transaction hash and status.
        """
        logger.info(f"[{self.task_id}] Executing swap: {amount_in} of {token_in_address} for {token_out_address}")
        await async_random_delay(5, 15)

        try:
            tx_hash = self.web3_client.swap_tokens(token_in_address, token_out_address, amount_in)

            if tx_hash:
                logger.info(f"[{self.task_id}] Swap successful. Tx Hash: {tx_hash}")

                # Log transaction to tracker
                self.tracker.log_transaction(
                    account_address=self.account_address,
                    task_id=self.task_id,
                    tx_type="swap",
                    tx_hash=tx_hash,
                    status="success",
                    amount=str(amount_in),
                    token_in=token_in_address,
                    token_out=token_out_address,
                    metadata={"swap_type": "dex"}
                )

                return {"status": "success", "tx_hash": tx_hash, "account": self.account_address}
            else:
                logger.error(f"[{self.task_id}] Swap failed for account {self.account_address}")

                # Log failed transaction
                self.tracker.log_transaction(
                    account_address=self.account_address,
                    task_id=self.task_id,
                    tx_type="swap",
                    status="failed",
                    error_message="Swap execution returned None"
                )

                return {"status": "failed", "account": self.account_address}

        except Exception as e:
            error_msg = str(e)
            logger.error(f"[{self.task_id}] Swap error: {error_msg}")

            # Log error transaction
            self.tracker.log_transaction(
                account_address=self.account_address,
                task_id=self.task_id,
                tx_type="swap",
                status="failed",
                error_message=error_msg
            )

            return {"status": "failed", "account": self.account_address, "error": error_msg}


if __name__ == "__main__":
    import asyncio
    import os
    from utils.logger import setup_logging
    setup_logging("DEBUG")

    async def main():
        dummy_private_key = os.getenv("PRIVATE_KEYS", "0x" + "1"*64).split(",")[0]
        dummy_rpc_url = os.getenv("WEB3_RPC_URL", "https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID")
        dummy_account_address = "0xAbc123Def456"

        if "YOUR_INFURA_PROJECT_ID" in dummy_rpc_url:
            logger.warning("Please set INFURA_PROJECT_ID in your .env file for a functional RPC URL.")

        swap_task = SwapTask(
            private_key=dummy_private_key,
            rpc_url=dummy_rpc_url,
            account_address=dummy_account_address,
            task_id="test_swap_001"
        )

        token_in = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
        token_out = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
        amount = 100000000000000000

        result = await swap_task.run(token_in_address=token_in, token_out_address=token_out, amount_in=amount)
        logger.info(f"Swap Task Result: {result}")

    asyncio.run(main())
