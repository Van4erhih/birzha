from typing import Optional, Dict, Any
from web3 import Web3
from eth_account.signers.local import LocalAccount
from loguru import logger
import json

# Uniswap V3 Router02 ABI (simplified for swap operations)
UNISWAP_ROUTER_ABI = json.loads('''[
    {
        "constant": false,
        "inputs": [
            {"name": "amountIn", "type": "uint256"},
            {"name": "amountOutMin", "type": "uint256"},
            {"name": "path", "type": "address[]"},
            {"name": "to", "type": "address"},
            {"name": "deadline", "type": "uint256"}
        ],
        "name": "swapExactTokensForTokens",
        "outputs": [{"name": "amounts", "type": "uint256[]"}],
        "type": "function"
    },
    {
        "constant": false,
        "inputs": [
            {"name": "amountOutMin", "type": "uint256"},
            {"name": "path", "type": "address[]"},
            {"name": "to", "type": "address"},
            {"name": "deadline", "type": "uint256"}
        ],
        "name": "swapExactETHForTokens",
        "outputs": [{"name": "amounts", "type": "uint256[]"}],
        "type": "function"
    }
]''')

# ERC-20 Approve ABI (simplified)
ERC20_ABI = json.loads('''[
    {
        "constant": false,
        "inputs": [
            {"name": "_spender", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": true,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    }
]''')


class DEXInteraction:
    """Handles real DEX swap operations on Uniswap V3."""

    UNISWAP_V3_ROUTER = "0xE592427A0AEce92De3Edee1F18E0157C05861564"  # Uniswap V3 Router on Ethereum
    WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"

    def __init__(self, w3: Web3, account: LocalAccount, config: Dict[str, Any]) -> None:
        """Initialize DEX interaction.

        Args:
            w3: Web3 instance.
            account: Ethereum account.
            config: Configuration dictionary.
        """
        self.w3 = w3
        self.account = account
        self.config = config
        self.router_contract = self.w3.eth.contract(
            address=self.w3.to_checksum_address(self.UNISWAP_V3_ROUTER),
            abi=UNISWAP_ROUTER_ABI
        )
        logger.info(f"DEXInteraction initialized for account {account.address}")

    def _build_swap_transaction(self, token_in: str, token_out: str, amount_in: int, min_amount_out: int = 0) -> Dict[str, Any]:
        """Build a swap transaction.

        Args:
            token_in: Input token address.
            token_out: Output token address.
            amount_in: Input amount.
            min_amount_out: Minimum output amount (slippage tolerance).

        Returns:
            Transaction dictionary.
        """
        path = [self.w3.to_checksum_address(token_in), self.w3.to_checksum_address(token_out)]
        nonce = self.w3.eth.get_transaction_count(self.account.address)
        gas_price = self.w3.eth.gas_price
        deadline = self.w3.eth.block_number + 200

        swap_function = self.router_contract.functions.swapExactTokensForTokens(
            amount_in,
            min_amount_out,
            path,
            self.account.address,
            deadline
        )

        transaction = swap_function.build_transaction({
            "from": self.account.address,
            "nonce": nonce,
            "gasPrice": gas_price,
            "gas": self.config.get("GAS_LIMIT", 300000),
            "chainId": self.w3.eth.chain_id
        })

        return transaction

    def swap_tokens(self, token_in: str, token_out: str, amount_in: int, min_amount_out: int = 0) -> Optional[str]:
        """Perform a token swap on Uniswap V3.

        Args:
            token_in: Input token address.
            token_out: Output token address.
            amount_in: Input amount.
            min_amount_out: Minimum output amount.

        Returns:
            Transaction hash if successful, None otherwise.
        """
        try:
            logger.info(f"Starting swap: {amount_in} of {token_in} -> {token_out}")

            # Check token balance
            token_contract = self.w3.eth.contract(
                address=self.w3.to_checksum_address(token_in),
                abi=ERC20_ABI
            )
            balance = token_contract.functions.balanceOf(self.account.address).call()
            if balance < amount_in:
                logger.error(f"Insufficient balance. Have: {balance}, Need: {amount_in}")
                return None

            # Approve token spending
            approve_tx = token_contract.functions.approve(
                self.UNISWAP_V3_ROUTER,
                amount_in
            ).build_transaction({
                "from": self.account.address,
                "nonce": self.w3.eth.get_transaction_count(self.account.address),
                "gasPrice": self.w3.eth.gas_price,
                "gas": 100000,
                "chainId": self.w3.eth.chain_id
            })

            signed_approve = self.w3.eth.account.sign_transaction(approve_tx, self.account.key)
            approve_hash = self.w3.eth.send_raw_transaction(signed_approve.rawTransaction)
            logger.info(f"Approval tx sent: {approve_hash.hex()}")

            # Build and send swap transaction
            swap_tx = self._build_swap_transaction(token_in, token_out, amount_in, min_amount_out)
            signed_swap = self.w3.eth.account.sign_transaction(swap_tx, self.account.key)
            swap_hash = self.w3.eth.send_raw_transaction(signed_swap.rawTransaction)

            logger.info(f"Swap transaction sent: {swap_hash.hex()}")
            return swap_hash.hex()

        except Exception as e:
            logger.error(f"Swap failed: {e}")
            return None


class BridgeInteraction:
    """Handles token bridge operations."""

    def __init__(self, w3: Web3, account: LocalAccount, config: Dict[str, Any]) -> None:
        """Initialize bridge interaction.

        Args:
            w3: Web3 instance.
            account: Ethereum account.
            config: Configuration dictionary.
        """
        self.w3 = w3
        self.account = account
        self.config = config
        logger.info(f"BridgeInteraction initialized for account {account.address}")

    def bridge_tokens(self, token_address: str, amount: int, from_chain_id: int, to_chain_id: int) -> Optional[str]:
        """Bridge tokens between chains (placeholder for Stargate, LayerZero, etc.).

        Args:
            token_address: Token to bridge.
            amount: Amount to bridge.
            from_chain_id: Source chain ID.
            to_chain_id: Destination chain ID.

        Returns:
            Transaction hash if successful, None otherwise.
        """
        try:
            logger.info(f"Bridging {amount} of {token_address} from chain {from_chain_id} to {to_chain_id}")

            # In production, integrate with Stargate, LayerZero, or other bridge protocols
            # For now, this is a placeholder that logs the bridge operation
            logger.info(f"Bridge operation would be sent for {token_address}")

            # Placeholder transaction hash
            return "0x" + "0" * 64

        except Exception as e:
            logger.error(f"Bridge failed: {e}")
            return None
