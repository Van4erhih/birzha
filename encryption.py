import os
import json
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken
from loguru import logger


class KeyEncryption:
    """Handles encryption/decryption of private keys."""

    KEY_FILE = ".keys_encryption_key"
    ENCRYPTED_ACCOUNTS_FILE = ".encrypted_accounts.json"

    @staticmethod
    def generate_encryption_key() -> str:
        """Generates a new encryption key."""
        key = Fernet.generate_key().decode()
        logger.info(f"Generated new encryption key")
        return key

    @staticmethod
    def save_encryption_key(key: str, key_file: str = KEY_FILE) -> None:
        """Saves the encryption key to a file (with restricted permissions).

        Args:
            key: The encryption key to save.
            key_file: Path to save the key file.
        """
        try:
            with open(key_file, 'w') as f:
                f.write(key)
            # Restrict permissions to owner only
            os.chmod(key_file, 0o600)
            logger.info(f"Encryption key saved to {key_file}")
        except Exception as e:
            logger.error(f"Failed to save encryption key: {e}")
            raise

    @staticmethod
    def load_encryption_key(key_file: str = KEY_FILE) -> Optional[str]:
        """Loads the encryption key from a file.

        Args:
            key_file: Path to the key file.

        Returns:
            The encryption key if found, None otherwise.
        """
        try:
            if not os.path.exists(key_file):
                logger.warning(f"Encryption key file not found: {key_file}")
                return None
            with open(key_file, 'r') as f:
                key = f.read().strip()
            logger.info(f"Encryption key loaded from {key_file}")
            return key
        except Exception as e:
            logger.error(f"Failed to load encryption key: {e}")
            return None

    @staticmethod
    def encrypt_private_key(private_key: str, encryption_key: str) -> str:
        """Encrypts a private key using Fernet symmetric encryption.

        Args:
            private_key: The private key to encrypt.
            encryption_key: The encryption key.

        Returns:
            The encrypted private key (hex-encoded).
        """
        try:
            cipher = Fernet(encryption_key.encode())
            encrypted = cipher.encrypt(private_key.encode())
            logger.debug(f"Private key encrypted successfully")
            return encrypted.hex()
        except Exception as e:
            logger.error(f"Failed to encrypt private key: {e}")
            raise

    @staticmethod
    def decrypt_private_key(encrypted_key_hex: str, encryption_key: str) -> str:
        """Decrypts an encrypted private key.

        Args:
            encrypted_key_hex: The encrypted private key (hex-encoded).
            encryption_key: The encryption key.

        Returns:
            The decrypted private key.
        """
        try:
            cipher = Fernet(encryption_key.encode())
            encrypted = bytes.fromhex(encrypted_key_hex)
            decrypted = cipher.decrypt(encrypted)
            logger.debug(f"Private key decrypted successfully")
            return decrypted.decode()
        except InvalidToken:
            logger.error("Invalid encryption key or corrupted encrypted data")
            raise
        except Exception as e:
            logger.error(f"Failed to decrypt private key: {e}")
            raise

    @staticmethod
    def encrypt_accounts_file(accounts_file: str, encryption_key: str, output_file: str = ENCRYPTED_ACCOUNTS_FILE) -> None:
        """Encrypts all private keys in an accounts file and saves to a new file.

        Args:
            accounts_file: Path to the file containing plaintext private keys.
            encryption_key: The encryption key.
            output_file: Path to save encrypted accounts.
        """
        try:
            accounts = []
            with open(accounts_file, 'r') as f:
                for line in f:
                    key = line.strip()
                    if key and not key.startswith('#'):
                        encrypted = KeyEncryption.encrypt_private_key(key, encryption_key)
                        accounts.append(encrypted)

            with open(output_file, 'w') as f:
                json.dump(accounts, f, indent=2)

            logger.info(f"Encrypted {len(accounts)} accounts and saved to {output_file}")
        except Exception as e:
            logger.error(f"Failed to encrypt accounts file: {e}")
            raise

    @staticmethod
    def decrypt_accounts_file(encrypted_file: str, encryption_key: str) -> list:
        """Decrypts all private keys from an encrypted accounts file.

        Args:
            encrypted_file: Path to the encrypted accounts file.
            encryption_key: The encryption key.

        Returns:
            List of decrypted private keys.
        """
        try:
            with open(encrypted_file, 'r') as f:
                encrypted_accounts = json.load(f)

            decrypted_accounts = []
            for encrypted_key_hex in encrypted_accounts:
                decrypted = KeyEncryption.decrypt_private_key(encrypted_key_hex, encryption_key)
                decrypted_accounts.append(decrypted)

            logger.info(f"Decrypted {len(decrypted_accounts)} accounts from {encrypted_file}")
            return decrypted_accounts
        except Exception as e:
            logger.error(f"Failed to decrypt accounts file: {e}")
            raise


if __name__ == "__main__":
    from utils.logger import setup_logging
    setup_logging("DEBUG")

    # Example usage
    key = KeyEncryption.generate_encryption_key()
    print(f"Generated key: {key[:20]}...")

    private_key = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
    encrypted = KeyEncryption.encrypt_private_key(private_key, key)
    print(f"Encrypted: {encrypted[:50]}...")

    decrypted = KeyEncryption.decrypt_private_key(encrypted, key)
    print(f"Decrypted: {decrypted}")
    assert decrypted == private_key, "Decryption failed!"
    print("✓ Encryption/Decryption test passed!")
