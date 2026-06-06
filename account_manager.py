import os
import random
from typing import List, Optional, Dict
from dotenv import load_dotenv
from loguru import logger

class AccountManager:
    """Manages loading and rotating accounts (private keys) and proxies."""

    def __init__(self, accounts_file: str = "data/accounts.txt", proxies_file: str = "data/proxies.txt") -> None:
        """Initializes the AccountManager.

        Args:
            accounts_file: Path to the file containing private keys.
            proxies_file: Path to the file containing proxy URLs.
        """
        load_dotenv() # Load environment variables from .env file
        self.accounts: List[str] = self._load_accounts(accounts_file)
        self.proxies: List[str] = self._load_proxies(proxies_file)
        self.account_index = 0
        self.proxy_index = 0
        logger.info(f"Loaded {len(self.accounts)} accounts and {len(self.proxies)} proxies.")

    def _load_accounts(self, filepath: str) -> List[str]:
        """Loads private keys from a file or environment variable."""
        accounts = []
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                accounts.extend([line.strip() for line in f if line.strip() and not line.strip().startswith('#')])
        
        # Also load from environment variable if available
        env_accounts = os.getenv("PRIVATE_KEYS")
        if env_accounts:
            accounts.extend([acc.strip() for acc in env_accounts.split(',') if acc.strip()])

        if not accounts:
            logger.warning(f"No accounts loaded from {filepath} or PRIVATE_KEYS environment variable.")
        return list(set(accounts)) # Remove duplicates

    def _load_proxies(self, filepath: str) -> List[str]:
        """Loads proxy URLs from a file or environment variable."""
        proxies = []
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                proxies.extend([line.strip() for line in f if line.strip() and not line.strip().startswith('#')])
        
        # Also load from environment variable if available
        env_proxies = os.getenv("PROXIES")
        if env_proxies:
            proxies.extend([p.strip() for p in env_proxies.split(',') if p.strip()])

        if not proxies:
            logger.warning(f"No proxies loaded from {filepath} or PROXIES environment variable. Operations might be performed without proxies.")
        return list(set(proxies)) # Remove duplicates

    def get_next_account(self) -> Optional[str]:
        """Returns the next account in a round-robin fashion."""
        if not self.accounts:
            return None
        account = self.accounts[self.account_index]
        self.account_index = (self.account_index + 1) % len(self.accounts)
        return account

    def get_random_account(self) -> Optional[str]:
        """Returns a random account."""
        if not self.accounts:
            return None
        return random.choice(self.accounts)

    def get_next_proxy(self) -> Optional[str]:
        """Returns the next proxy in a round-robin fashion."""
        if not self.proxies:
            return None
        proxy = self.proxies[self.proxy_index]
        self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return proxy

    def get_random_proxy(self) -> Optional[str]:
        """Returns a random proxy."""
        if not self.proxies:
            return None
        return random.choice(self.proxies)

    def get_account_proxy_pair(self) -> Dict[str, Optional[str]]:
        """Returns a dictionary with a randomly selected account and proxy."""
        account = self.get_random_account()
        proxy = self.get_random_proxy()
        return {"account": account, "proxy": proxy}

if __name__ == "__main__":
    # Example usage
    from utils.logger import setup_logging
    setup_logging("DEBUG")

    # Create dummy files for testing
    os.makedirs("data", exist_ok=True)
    with open("data/accounts.txt", "w") as f:
        f.write("0xAccount1PrivateKey\n0xAccount2PrivateKey\n")
    with open("data/proxies.txt", "w") as f:
        f.write("http://user:pass@1.1.1.1:8080\nsocks5://user2:pass2@2.2.2.2:9090\n")

    manager = AccountManager()
    print(f"Accounts: {manager.accounts}")
    print(f"Proxies: {manager.proxies}")

    for _ in range(3):
        pair = manager.get_account_proxy_pair()
        print(f"Random pair: {pair}")

    # Clean up dummy files
    os.remove("data/accounts.txt")
    os.remove("data/proxies.txt")
    os.rmdir("data")
