from typing import Any, Dict
from loguru import logger

from tasks.base_task import BaseTask
from core.web3_wrapper import Web3Wrapper
from utils.helpers import retry, async_random_delay
from utils.transaction_tracker import TransactionTracker


class BridgeTask(BaseTask):
    """Task for bridging tokens between different blockchain networks."""

    def __init__(self, private_key: str, rpc_url: str, account_address: str, proxy: str = None, task_id: str = None) -> None:
        super().__init__(private_key, rpc_url, account_address, proxy, task_id)
        self.web3_client = Web3Wrapper(private_key=private_key, rpc_url=rpc_url)
        self.tracker = TransactionTracker()

    @retry(attempts=3, delay=10, backoff=1.5)
    async def execute(self, token_address: str, amount: int, from_chain_id: int, to_chain_id: int) -> Dict[str, Any]:
        """Executes the token bridging operation with transaction tracking.

        Args:
            token_address: The address of the token to bridge.
            amount: The amount of tokens to bridge (in smallest unit).
            from_chain_id: The source chain ID.
            to_chain_id: The destination chain ID.

        Returns:
            A dictionary containing the transaction hash and status.
        """
        logger.info(f"[{self.task_id}] Bridging {amount} of {token_address} from chain {from_chain_id} to {to_chain_id}")
        await async_random_delay(5, 15)

        try:
            tx_hash = self.web3_client.bridge_tokens(token_address, amount, from_chain_id, to_chain_id)

            if tx_hash:
                logger.info(f"[{self.task_id}] Bridge successful. Tx Hash: {tx_hash}")

                # Log transaction to tracker
                self.tracker.log_transaction(
                    account_address=self.account_address,
                    task_id=self.task_id,
                    tx_type="bridge",
                    tx_hash=tx_hash,
                    status="success",
                    amount=str(amount),
                    token_in=token_address,
                    from_chain=from_chain_id,
                    to_chain=to_chain_id,
                    metadata={"bridge_type": "cross_chain"}
                )

                return {"status": "success", "tx_hash": tx_hash, "account": self.account_address}
            else:
                logger.error(f"[{self.task_id}] Bridge failed for account {self.account_address}")

                # Log failed transaction
                self.tracker.log_transaction(
                    account_address=self.account_address,
                    task_id=self.task_id,
                    tx_type="bridge",
                    status="failed",
                    error_message="Bridge execution returned None"
                )

                return {"status": "failed", "account": self.account_address}

        except Exception as e:
            error_msg = str(e)
            logger.error(f"[{self.task_id}] Bridge error: {error_msg}")

            # Log error transaction
            self.tracker.log_transaction(
                account_address=self.account_address,
                task_id=self.task_id,
                tx_type="bridge",
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

        bridge_task = BridgeTask(
            private_key=dummy_private_key,
            rpc_url=dummy_rpc_url,
            account_address=dummy_account_address,
            task_id="test_bridge_001"
        )

        token = "0x...token_address..."
        amount = 1000000000000000000
        from_chain = 1
        to_chain = 137

        result = await bridge_task.run(token_address=token, amount=amount, from_chain_id=from_chain, to_chain_id=to_chain)
        logger.info(f"Bridge Task Result: {result}")

    asyncio.run(main())
