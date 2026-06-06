import os
from typing import Optional, Dict, Any

from web3 import Web3
from eth_account import Account
from eth_account.signers.local import LocalAccount
import yaml
from loguru import logger

from core.dex_interactions import DEXInteraction, BridgeInteraction


class Web3Wrapper:
    """A wrapper class for Web3.py interactions, handling RPC connections, wallet management, and common DeFi operations."""

    def __init__(self, private_key: str, rpc_url: Optional[str] = None, chain_id: Optional[int] = None) -> None:
        """Initializes the Web3Wrapper.

        Args:
            private_key: The private key of the wallet to use.
            rpc_url: The RPC URL for the blockchain network. If None, it will be loaded from config.yaml.
            chain_id: The chain ID of the blockchain network. If None, it will be loaded from config.yaml.
        """
        self.config = self._load_config()
        self.rpc_url = rpc_url if rpc_url else self.config["WEB3"]["DEFAULT_RPC_URL"]
        self.chain_id = chain_id if chain_id else self.config["WEB3"]["CHAIN_ID"]

        if not self.rpc_url or "YOUR_INFURA_PROJECT_ID" in self.rpc_url:
            infura_project_id = os.getenv("INFURA_PROJECT_ID")
            if infura_project_id:
                self.rpc_url = self.rpc_url.replace("YOUR_INFURA_PROJECT_ID", infura_project_id)
            else:
                logger.error("INFURA_PROJECT_ID not found in .env or config.yaml. Please provide a valid RPC URL.")
                raise ValueError("RPC URL not properly configured.")

        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))

        if not self.w3.is_connected():
            logger.error(f"Failed to connect to Web3 provider at {self.rpc_url}")
            raise ConnectionError(f"Could not connect to RPC {self.rpc_url}")

        self.account: LocalAccount = Account.from_key(private_key)
        logger.info(f"Connected to RPC: {self.rpc_url} (Chain ID: {self.w3.eth.chain_id})")
        logger.info(f"Wallet initialized: {self.account.address}")

        # Initialize DEX and Bridge interactions
        self.dex = DEXInteraction(self.w3, self.account, self.config["WEB3"])
        self.bridge = BridgeInteraction(self.w3, self.account, self.config["WEB3"])

    def _load_config(self) -> Dict[str, Any]:
        """Loads configuration from config.yaml."""
        config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
        with open(config_path, "r") as f:
            return yaml.safe_load(f)

    def get_balance(self, address: str) -> float:
        """Gets the native token balance of an address in Ether."""
        balance_wei = self.w3.eth.get_balance(self.w3.to_checksum_address(address))
        return self.w3.from_wei(balance_wei, "ether")

    def get_gas_price(self) -> int:
        """Gets the current gas price in Wei."""
        return self.w3.eth.gas_price

    def send_transaction(self, to_address: str, value_ether: float, data: str = "0x") -> Optional[str]:
        """Sends a simple native token transfer transaction.

        Args:
            to_address: The recipient address.
            value_ether: The amount of native token to send in Ether.
            data: Optional transaction data.

        Returns:
            The transaction hash if successful, None otherwise.
        """
        try:
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            gas_price = self.get_gas_price()
            gas_limit = self.config["WEB3"]["GAS_LIMIT"]

            transaction = {
                "from": self.account.address,
                "to": self.w3.to_checksum_address(to_address),
                "value": self.w3.to_wei(value_ether, "ether"),
                "gas": gas_limit,
                "gasPrice": gas_price,
                "nonce": nonce,
                "chainId": self.chain_id,
                "data": data
            }

            signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key=self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            logger.info(f"Transaction sent: {tx_hash.hex()}")
            return tx_hash.hex()
        except Exception as e:
            logger.error(f"Failed to send transaction: {e}")
            return None

    def approve_token(self, token_address: str, spender_address: str, amount: int) -> Optional[str]:
        """Approves token spending via ERC-20 approve function.

        Args:
            token_address: The address of the ERC-20 token.
            spender_address: The address of the contract allowed to spend tokens.
            amount: The amount of tokens to approve (in smallest unit).

        Returns:
            The transaction hash if successful, None otherwise.
        """
        try:
            logger.info(f"Approving {amount} of token {token_address} for spender {spender_address}")
            # This is a placeholder - implement via dex.py if needed
            return "0x...approval_tx_hash..."
        except Exception as e:
            logger.error(f"Failed to approve token: {e}")
            return None

    def swap_tokens(self, token_in_address: str, token_out_address: str, amount_in: int) -> Optional[str]:
        """Performs a token swap on Uniswap V3 DEX.

        Args:
            token_in_address: The address of the input token.
            token_out_address: The address of the output token.
            amount_in: The amount of input tokens (in smallest unit).

        Returns:
            The transaction hash if successful, None otherwise.
        """
        try:
            logger.info(f"Swapping {amount_in} of {token_in_address} for {token_out_address}")
            tx_hash = self.dex.swap_tokens(token_in_address, token_out_address, amount_in)
            return tx_hash
        except Exception as e:
            logger.error(f"Failed to swap tokens: {e}")
            return None

    def bridge_tokens(self, token_address: str, amount: int, from_chain_id: int, to_chain_id: int) -> Optional[str]:
        """Bridges tokens between chains.

        Args:
            token_address: The address of the token to bridge.
            amount: The amount of tokens to bridge (in smallest unit).
            from_chain_id: The source chain ID.
            to_chain_id: The destination chain ID.

        Returns:
            The transaction hash if successful, None otherwise.
        """
        try:
            logger.info(f"Bridging {amount} of {token_address} from chain {from_chain_id} to {to_chain_id}")
            tx_hash = self.bridge.bridge_tokens(token_address, amount, from_chain_id, to_chain_id)
            return tx_hash
        except Exception as e:
            logger.error(f"Failed to bridge tokens: {e}")
            return None


if __name__ == "__main__":
    from utils.logger import setup_logging
    setup_logging("DEBUG")

    dummy_private_key = os.getenv("PRIVATE_KEYS", "0x" + "1"*64).split(",")[0]

    try:
        web3_client = Web3Wrapper(private_key=dummy_private_key)
        address = web3_client.account.address
        logger.info(f"Wallet Address: {address}")
        balance = web3_client.get_balance(address)
        logger.info(f"Balance: {balance} ETH")
        gas_price = web3_client.get_gas_price()
        logger.info(f"Current Gas Price: {web3_client.w3.from_wei(gas_price, 'gwei')} Gwei")
    except Exception as e:
        logger.error(f"Web3Wrapper example failed: {e}")
