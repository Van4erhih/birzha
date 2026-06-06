import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from loguru import logger
import sqlite3


class TransactionTracker:
    """Tracks and logs all transaction operations."""

    def __init__(self, db_path: str = "transaction_history.db") -> None:
        """Initialize the transaction tracker with SQLite database.

        Args:
            db_path: Path to the SQLite database file.
        """
        self.db_path = db_path
        self._init_database()
        logger.info(f"TransactionTracker initialized with database: {db_path}")

    def _init_database(self) -> None:
        """Initialize the SQLite database schema."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    account_address TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    tx_hash TEXT,
                    tx_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    amount TEXT,
                    token_in TEXT,
                    token_out TEXT,
                    from_chain INTEGER,
                    to_chain INTEGER,
                    gas_used TEXT,
                    gas_price TEXT,
                    error_message TEXT,
                    metadata TEXT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS task_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    account_address TEXT NOT NULL,
                    task_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    result TEXT,
                    error_message TEXT
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_account ON transactions(account_address)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_task_id ON transactions(task_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp ON transactions(timestamp)
            """)

            conn.commit()
            conn.close()
            logger.debug("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def log_transaction(
        self,
        account_address: str,
        task_id: str,
        tx_type: str,
        tx_hash: Optional[str] = None,
        status: str = "pending",
        amount: Optional[str] = None,
        token_in: Optional[str] = None,
        token_out: Optional[str] = None,
        from_chain: Optional[int] = None,
        to_chain: Optional[int] = None,
        gas_used: Optional[str] = None,
        gas_price: Optional[str] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """Log a transaction to the database.

        Args:
            account_address: The wallet address performing the transaction.
            task_id: The task ID associated with the transaction.
            tx_type: Type of transaction (swap, bridge, transfer, etc.).
            tx_hash: Transaction hash on blockchain.
            status: Transaction status (pending, success, failed).
            amount: Amount involved.
            token_in: Input token address.
            token_out: Output token address.
            from_chain: Source chain ID.
            to_chain: Destination chain ID.
            gas_used: Gas used in the transaction.
            gas_price: Gas price used.
            error_message: Error message if transaction failed.
            metadata: Additional metadata as dictionary.

        Returns:
            The transaction ID in the database.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            timestamp = datetime.utcnow().isoformat()
            metadata_json = json.dumps(metadata) if metadata else None

            cursor.execute("""
                INSERT INTO transactions (
                    timestamp, account_address, task_id, tx_hash, tx_type, status,
                    amount, token_in, token_out, from_chain, to_chain,
                    gas_used, gas_price, error_message, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                timestamp, account_address, task_id, tx_hash, tx_type, status,
                amount, token_in, token_out, from_chain, to_chain,
                gas_used, gas_price, error_message, metadata_json
            ))

            conn.commit()
            tx_id = cursor.lastrowid
            conn.close()

            logger.info(f"Transaction logged: {tx_type} - {status} (ID: {tx_id})")
            return tx_id
        except Exception as e:
            logger.error(f"Failed to log transaction: {e}")
            raise

    def log_task(
        self,
        task_id: str,
        account_address: str,
        task_type: str,
        status: str,
        result: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> int:
        """Log a task execution to the database.

        Args:
            task_id: Unique task ID.
            account_address: The wallet address.
            task_type: Type of task (swap_task, bridge_task, airdrop_task).
            status: Task status (success, failed, completed).
            result: Task result as dictionary.
            error_message: Error message if task failed.

        Returns:
            The task log ID in the database.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            timestamp = datetime.utcnow().isoformat()
            result_json = json.dumps(result) if result else None

            cursor.execute("""
                INSERT INTO task_logs (
                    timestamp, task_id, account_address, task_type, status, result, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                timestamp, task_id, account_address, task_type, status, result_json, error_message
            ))

            conn.commit()
            log_id = cursor.lastrowid
            conn.close()

            logger.info(f"Task logged: {task_type} - {status} (ID: {log_id})")
            return log_id
        except Exception as e:
            logger.error(f"Failed to log task: {e}")
            raise

    def get_account_history(self, account_address: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve transaction history for an account.

        Args:
            account_address: The wallet address.
            limit: Maximum number of records to return.

        Returns:
            List of transaction records.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM transactions
                WHERE account_address = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (account_address, limit))

            rows = cursor.fetchall()
            conn.close()

            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to retrieve account history: {e}")
            return []

    def get_task_statistics(self, task_id: str) -> Dict[str, Any]:
        """Get statistics for a specific task.

        Args:
            task_id: The task ID.

        Returns:
            Dictionary containing task statistics.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    COUNT(*) as total_txs,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending
                FROM transactions
                WHERE task_id = ?
            """, (task_id,))

            result = cursor.fetchone()
            conn.close()

            return {
                "task_id": task_id,
                "total_transactions": result[0] or 0,
                "successful": result[1] or 0,
                "failed": result[2] or 0,
                "pending": result[3] or 0,
                "success_rate": (result[1] or 0) / (result[0] or 1) * 100
            }
        except Exception as e:
            logger.error(f"Failed to get task statistics: {e}")
            return {}

    def export_to_csv(self, output_file: str = "transaction_export.csv") -> None:
        """Export transaction history to CSV file.

        Args:
            output_file: Path to the output CSV file.
        """
        try:
            import csv
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM transactions ORDER BY timestamp DESC")
            rows = cursor.fetchall()
            conn.close()

            if not rows:
                logger.warning("No transactions to export")
                return

            keys = rows[0].keys()
            with open(output_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                for row in rows:
                    writer.writerow(dict(row))

            logger.info(f"Transactions exported to {output_file}")
        except Exception as e:
            logger.error(f"Failed to export transactions: {e}")
            raise

    def cleanup_old_records(self, days: int = 30) -> int:
        """Delete transaction records older than specified days.

        Args:
            days: Number of days to keep (delete older records).

        Returns:
            Number of deleted records.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                DELETE FROM transactions
                WHERE datetime(timestamp) < datetime('now', '-' || ? || ' days')
            """, (days,))

            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()

            logger.info(f"Deleted {deleted_count} records older than {days} days")
            return deleted_count
        except Exception as e:
            logger.error(f"Failed to cleanup old records: {e}")
            raise


if __name__ == "__main__":
    from utils.logger import setup_logging
    setup_logging("DEBUG")

    tracker = TransactionTracker()

    # Example: Log a transaction
    tx_id = tracker.log_transaction(
        account_address="0x1234567890123456789012345678901234567890",
        task_id="swap_task_001",
        tx_type="swap",
        tx_hash="0xabcdef1234567890",
        status="success",
        amount="1000000000000000000",
        token_in="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        token_out="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        gas_used="150000",
        gas_price="50",
        metadata={"slippage": 0.5}
    )
    logger.info(f"Logged transaction with ID: {tx_id}")

    # Example: Log a task
    task_id = tracker.log_task(
        task_id="swap_task_001",
        account_address="0x1234567890123456789012345678901234567890",
        task_type="swap_task",
        status="completed",
        result={"tx_hashes": ["0xabcdef1234567890"]},
    )
    logger.info(f"Logged task with ID: {task_id}")

    # Example: Get account history
    history = tracker.get_account_history("0x1234567890123456789012345678901234567890", limit=10)
    logger.info(f"Account history: {history}")

    # Example: Get task statistics
    stats = tracker.get_task_statistics("swap_task_001")
    logger.info(f"Task statistics: {stats}")
