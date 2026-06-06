from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from loguru import logger


class BaseTask(ABC):
    """Abstract base class for all farming tasks."""

    def __init__(self, private_key: str, rpc_url: str, account_address: str, proxy: Optional[str] = None, task_id: Optional[str] = None) -> None:
        """Initializes the base task.

        Args:
            private_key: The private key of the account.
            rpc_url: The RPC URL for blockchain interaction.
            account_address: The blockchain address associated with this task.
            proxy: The proxy URL to use for this task, if any.
            task_id: A unique identifier for the task instance.
        """
        self.private_key = private_key
        self.rpc_url = rpc_url
        self.account_address = account_address
        self.proxy = proxy
        self.task_id = task_id if task_id else f"task_{account_address[:6]}_{id(self)}"
        logger.info(f"Task {self.task_id} initialized for account {self.account_address}")

    @abstractmethod
    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        """Executes the specific farming task.

        This method must be implemented by all concrete task classes.

        Args:
            **kwargs: Arbitrary keyword arguments for task execution.

        Returns:
            A dictionary containing the results of the task execution.
        """
        pass

    async def run(self, **kwargs: Any) -> Dict[str, Any]:
        """Wrapper method to execute the task and handle common logging/error reporting."""
        logger.info(f"Starting task {self.task_id} for account {self.account_address}")
        try:
            result = await self.execute(**kwargs)
            logger.success(f"Task {self.task_id} completed successfully for account {self.account_address}")
            return result
        except Exception as e:
            logger.error(f"Task {self.task_id} failed for account {self.account_address}: {e}")
            return {"status": "failed", "error": str(e), "account": self.account_address}
