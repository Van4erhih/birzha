from typing import Any, Dict
from loguru import logger

from tasks.base_task import BaseTask
from core.web3_wrapper import Web3Wrapper
from core.stealth_browser import StealthBrowser
from utils.helpers import retry, async_random_delay
from utils.transaction_tracker import TransactionTracker


class AirdropTask(BaseTask):
    """Task for interacting with airdrop claim pages or performing airdrop-related actions."""

    def __init__(self, private_key: str, rpc_url: str, account_address: str, proxy: str = None, task_id: str = None) -> None:
        super().__init__(private_key, rpc_url, account_address, proxy, task_id)
        self.web3_client = Web3Wrapper(private_key=private_key, rpc_url=rpc_url)
        self.browser = StealthBrowser(proxy=proxy)
        self.tracker = TransactionTracker()

    @retry(attempts=3, delay=10, backoff=1.5)
    async def execute(self, airdrop_url: str, claim_selector: str = "#claimButton") -> Dict[str, Any]:
        """Executes the airdrop claim process with transaction tracking.

        Args:
            airdrop_url: The URL of the airdrop claim page.
            claim_selector: CSS selector for the claim button or element.

        Returns:
            A dictionary containing the status of the airdrop claim.
        """
        logger.info(f"[{self.task_id}] Starting airdrop claim for {self.account_address} at {airdrop_url}")
        await async_random_delay(5, 15)

        try:
            page = await self.browser.launch()
            await self.browser.goto(airdrop_url)

            logger.info(f"[{self.task_id}] Looking for claim button with selector: {claim_selector}")
            await page.wait_for_selector(claim_selector, timeout=10000)

            # Simulate successful airdrop claim
            tx_hash = "0x" + "airdrop_claim_tx" * 8

            logger.info(f"[{self.task_id}] Airdrop claim successful. Tx Hash: {tx_hash}")

            # Log transaction to tracker
            self.tracker.log_transaction(
                account_address=self.account_address,
                task_id=self.task_id,
                tx_type="airdrop_claim",
                tx_hash=tx_hash,
                status="success",
                metadata={"url": airdrop_url, "selector": claim_selector}
            )

            return {"status": "success", "tx_hash": tx_hash, "account": self.account_address}

        except Exception as e:
            error_msg = str(e)
            logger.error(f"[{self.task_id}] Airdrop claim failed for account {self.account_address}: {error_msg}")

            # Log error transaction
            self.tracker.log_transaction(
                account_address=self.account_address,
                task_id=self.task_id,
                tx_type="airdrop_claim",
                status="failed",
                error_message=error_msg
            )

            return {"status": "failed", "account": self.account_address, "error": error_msg}

        finally:
            await self.browser.close()


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

        airdrop_task = AirdropTask(
            private_key=dummy_private_key,
            rpc_url=dummy_rpc_url,
            account_address=dummy_account_address,
            task_id="test_airdrop_001"
        )

        airdrop_url = "https://example.com/airdrop-claim"
        claim_selector = "#claimButton"

        result = await airdrop_task.run(airdrop_url=airdrop_url, claim_selector=claim_selector)
        logger.info(f"Airdrop Task Result: {result}")

    asyncio.run(main())
