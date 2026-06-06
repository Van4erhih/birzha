import asyncio
import yaml
import os
from loguru import logger

from utils.logger import setup_logging
from core.task_orchestrator import TaskOrchestrator
from tasks.swap_task import SwapTask
from tasks.bridge_task import BridgeTask
from tasks.airdrop_task import AirdropTask

async def main():
    """Main function to set up and run the Crypto Farming Orchestrator."""
    
    # Load configuration
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    # Setup logging
    setup_logging(log_level=config["LOG_LEVEL"], log_file=f"{config['APP_NAME'].lower()}.log")
    logger.info(f"Starting {config["APP_NAME"]}")

    orchestrator = TaskOrchestrator(config_path=config_path)

    # --- Example Usage of Tasks ---

    # Example 1: Running SwapTasks sequentially
    logger.info("\n--- Running SwapTasks Sequentially ---")
    swap_task_args = [
        {"token_in_address": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", "token_out_address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", "amount_in": 10000000000000000},
        {"token_in_address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", "token_out_address": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", "amount_in": 50000000},
    ]
    sequential_swap_results = await orchestrator.run_tasks_sequentially(SwapTask, swap_task_args)
    for res in sequential_swap_results:
        logger.info(f"Sequential Swap Result: {res}")

    # Example 2: Running BridgeTasks in parallel
    logger.info("\n--- Running BridgeTasks in Parallel ---")
    bridge_task_args = [
        {"token_address": "0x...", "amount": 1000000000000000000, "from_chain_id": 1, "to_chain_id": 137},
        {"token_address": "0x...", "amount": 500000000000000000, "from_chain_id": 137, "to_chain_id": 1},
    ]
    parallel_bridge_results = await orchestrator.run_tasks_in_parallel(BridgeTask, bridge_task_args)
    for res in parallel_bridge_results:
        logger.info(f"Parallel Bridge Result: {res}")

    # Example 3: Running AirdropTasks in parallel
    logger.info("\n--- Running AirdropTasks in Parallel ---")
    airdrop_task_args = [
        {"airdrop_url": "https://example.com/airdrop-claim-1", "claim_selector": "#claimBtn1"},
        {"airdrop_url": "https://example.com/airdrop-claim-2", "claim_selector": "#claimBtn2"},
        {"airdrop_url": "https://example.com/airdrop-claim-3", "claim_selector": "#claimBtn3"},
    ]
    parallel_airdrop_results = await orchestrator.run_tasks_in_parallel(AirdropTask, airdrop_task_args)
    for res in parallel_airdrop_results:
        logger.info(f"Parallel Airdrop Result: {res}")

    logger.info(f"{config["APP_NAME"]} finished.")

if __name__ == "__main__":
    asyncio.run(main())
