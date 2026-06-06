import os
import asyncio
import random
from typing import List, Dict, Any, Type, Optional

from loguru import logger
from web3 import Web3
import yaml

from core.account_manager import AccountManager
from tasks.base_task import BaseTask
from utils.helpers import async_random_delay

class TaskOrchestrator:
    """The central engine for orchestrating and executing farming tasks across multiple accounts."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initializes the TaskOrchestrator.

        Args:
            config_path: Path to the configuration file.
        """
        self.config = self._load_config(config_path)
        self.account_manager = AccountManager(
            accounts_file=os.path.join(os.path.dirname(__file__), "..", "data", "accounts.txt"),
            proxies_file=os.path.join(os.path.dirname(__file__), "..", "data", "proxies.txt")
        )
        self.max_parallel_tasks = self.config["ORCHESTRATOR"]["MAX_PARALLEL_TASKS"]
        self.min_delay = self.config["ORCHESTRATOR"]["MIN_DELAY_SECONDS"]
        self.max_delay = self.config["ORCHESTRATOR"]["MAX_DELAY_SECONDS"]
        logger.info("TaskOrchestrator initialized.")

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Loads configuration from config.yaml."""
        with open(config_path, "r") as f:
            return yaml.safe_load(f)

    async def _execute_single_task(self, task_class: Type[BaseTask], private_key: str, account_address: str, proxy: Optional[str], task_kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Executes a single task instance.

        Args:
            task_class: The class of the task to execute.
            private_key: The private key for the account.
            account_address: The public address of the account.
            proxy: The proxy URL for the task.
            task_kwargs: Keyword arguments specific to the task.

        Returns:
            A dictionary containing the task execution result.
        """
        task_id = f"{task_class.__name__}_{account_address[:6]}_{random.randint(1000, 9999)}"
        rpc_url = self.config["WEB3"]["DEFAULT_RPC_URL"]
        
        try:
            task_instance = task_class(
                private_key=private_key,
                rpc_url=rpc_url,
                account_address=account_address,
                proxy=proxy,
                task_id=task_id
            )
            result = await task_instance.run(**task_kwargs)
            return result
        except Exception as e:
            logger.error(f"Error executing task {task_id} for account {account_address}: {e}")
            return {"status": "failed", "account": account_address, "error": str(e)}

    async def run_tasks_sequentially(self, task_class: Type[BaseTask], task_kwargs_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Runs tasks sequentially with random delays between each task.

        Args:
            task_class: The class of the task to execute.
            task_kwargs_list: A list of dictionaries, each containing keyword arguments for a task.

        Returns:
            A list of dictionaries, each representing the result of a task.
        """
        results = []
        for i, task_kwargs in enumerate(task_kwargs_list):
            account_data = self.account_manager.get_account_proxy_pair()
            private_key = account_data["account"]
            proxy = account_data["proxy"]
            account_address = Web3(Web3.HTTPProvider(self.config["WEB3"]["DEFAULT_RPC_URL"])).eth.account.from_key(private_key).address if private_key else ""

            if not private_key:
                logger.error("No account available for sequential task execution. Skipping.")
                results.append({"status": "skipped", "error": "No account available"})
                continue

            logger.info(f"Executing sequential task {i+1}/{len(task_kwargs_list)} for account {account_address}")
            result = await self._execute_single_task(task_class, private_key, account_address, proxy, task_kwargs)
            results.append(result)
            await async_random_delay(self.min_delay, self.max_delay)
        return results

    async def run_tasks_in_parallel(self, task_class: Type[BaseTask], task_kwargs_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Runs tasks in parallel, respecting the maximum parallel tasks limit.

        Args:
            task_class: The class of the task to execute.
            task_kwargs_list: A list of dictionaries, each containing keyword arguments for a task.

        Returns:
            A list of dictionaries, each representing the result of a task.
        """
        tasks = []
        results = []
        semaphore = asyncio.Semaphore(self.max_parallel_tasks)

        async def semaphored_task(private_key: str, account_address: str, proxy: Optional[str], task_kwargs: Dict[str, Any]):
            async with semaphore:
                await async_random_delay(self.min_delay, self.max_delay) # Delay before starting each parallel task
                return await self._execute_single_task(task_class, private_key, account_address, proxy, task_kwargs)

        for task_kwargs in task_kwargs_list:
            account_data = self.account_manager.get_account_proxy_pair()
            private_key = account_data["account"]
            proxy = account_data["proxy"]
            account_address = Web3(Web3.HTTPProvider(self.config["WEB3"]["DEFAULT_RPC_URL"])).eth.account.from_key(private_key).address if private_key else ""

            if not private_key:
                logger.error("No account available for parallel task execution. Skipping.")
                results.append({"status": "skipped", "error": "No account available"})
                continue

            tasks.append(semaphored_task(private_key, account_address, proxy, task_kwargs))

        results = await asyncio.gather(*tasks)
        return results

if __name__ == "__main__":
    import asyncio
    from utils.logger import setup_logging
    from tasks.swap_task import SwapTask
    from tasks.airdrop_task import AirdropTask

    setup_logging("DEBUG")

    async def main():
        # Create dummy files for testing if they don't exist
        os.makedirs("data", exist_ok=True)
        if not os.path.exists("data/accounts.txt"):
            with open("data/accounts.txt", "w") as f:
                f.write("0x" + "1"*64 + "\n")
                f.write("0x" + "2"*64 + "\n")
        if not os.path.exists("data/proxies.txt"):
            with open("data/proxies.txt", "w") as f:
                f.write("http://user:pass@1.1.1.1:8080\n")
                f.write("socks5://user2:pass2@2.2.2.2:9090\n")

        orchestrator = TaskOrchestrator()

        # Example: Running SwapTasks sequentially
        logger.info("\n--- Running SwapTasks Sequentially ---")
        swap_task_args = [
            {"token_in_address": "0x...", "token_out_address": "0x...", "amount_in": 100},
            {"token_in_address": "0x...", "token_out_address": "0x...", "amount_in": 200},
        ]
        sequential_swap_results = await orchestrator.run_tasks_sequentially(SwapTask, swap_task_args)
        for res in sequential_swap_results:
            logger.info(f"Sequential Swap Result: {res}")

        # Example: Running AirdropTasks in parallel
        logger.info("\n--- Running AirdropTasks in Parallel ---")
        airdrop_task_args = [
            {"airdrop_url": "https://example.com/airdrop1", "claim_selector": "#claimBtn1"},
            {"airdrop_url": "https://example.com/airdrop2", "claim_selector": "#claimBtn2"},
            {"airdrop_url": "https://example.com/airdrop3", "claim_selector": "#claimBtn3"},
        ]
        parallel_airdrop_results = await orchestrator.run_tasks_in_parallel(AirdropTask, airdrop_task_args)
        for res in parallel_airdrop_results:
            logger.info(f"Parallel Airdrop Result: {res}")

        # Clean up dummy files
        os.remove("data/accounts.txt")
        os.remove("data/proxies.txt")
        os.rmdir("data")

    asyncio.run(main())
