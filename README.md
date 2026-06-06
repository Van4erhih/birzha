# Crypto Farming Orchestrator

This project provides a modular and scalable boilerplate for automating Web3 interactions, designed for crypto farming, airdrop hunting, and similar multi-account operations. It leverages Python, Playwright for browser automation, and Web3.py for blockchain interactions, with built-in support for proxy and session rotation.

## Features

- **Modular Structure**: Cleanly separated into logical modules for easy maintenance and extension.
- **Account & Proxy Management**: Handles loading, rotation, and unique session fingerprints.
- **Web3 Integration**: Boilerplate for RPC connections, wallet management, and placeholder methods for common DeFi actions.
- **Stealth Automation**: Basic anti-detect header initialization for browser automation.
- **Task Orchestration**: Central engine for parallel/sequential task execution with anti-sybil delays.
- **Robust Logging & Error Handling**: Comprehensive logging and error handling for network issues and failed transactions.
- **Type Hinting & Docstrings**: Improves code readability and maintainability.

## Project Structure

```
crypto_farming_orchestrator/
├── main.py                    # Entry point / Task Orchestrator
├── config.yaml                # Configuration file
├── .env.example               # Environment variables template
├── requirements.txt           # Dependencies
├── README.md                  # Setup & usage instructions
├── data/
│   ├── accounts.txt           # Account data (private keys)
│   └── proxies.txt            # Proxy list
├── core/
│   ├── __init__.py
│   ├── account_manager.py     # Account & Proxy Manager
│   ├── web3_wrapper.py        # Web3 Module Wrapper
│   ├── stealth_browser.py     # Stealth Automation Wrapper (Playwright)
│   └── task_orchestrator.py   # Task Orchestrator logic
├── tasks/
│   ├── __init__.py
│   ├── base_task.py           # Abstract base task class
│   ├── swap_task.py           # Example: DEX swap task
│   ├── bridge_task.py         # Example: Bridge task
│   └── airdrop_task.py        # Example: Airdrop interaction task
├── utils/
│   ├── __init__.py
│   ├── logger.py              # Logging configuration
│   ├── helpers.py             # Random delays, retry decorators
│   └── fingerprint.py         # Browser fingerprint generation
└── logs/
    └── .gitkeep
```

## Setup Instructions

1.  **Clone the repository**:

    ```bash
    git clone https://github.com/your-username/crypto-farming-orchestrator.git
    cd crypto-farming-orchestrator
    ```

2.  **Create and activate a virtual environment** (recommended):

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies**:

    ```bash
    pip install -r requirements.txt
    playwright install
    ```

4.  **Configure environment variables**:

    Copy `.env.example` to `.env` and fill in your private keys, proxy details, and API keys.

    ```bash
    cp .env.example .env
    ```

    Edit the `.env` file:

    ```ini
    # .env
    PRIVATE_KEYS="0x...your_private_key_1...,0x...your_private_key_2..."
    PROXIES="http://user:pass@ip:port,socks5://user:pass@ip:port"
    INFURA_PROJECT_ID="YOUR_INFURA_PROJECT_ID"
    ```

5.  **Configure `config.yaml`**:

    Adjust general settings, Web3 parameters, Playwright options, and orchestrator behavior in `config.yaml`.

6.  **Prepare data files**:

    Populate `data/accounts.txt` with one private key per line and `data/proxies.txt` with one proxy URL per line.

    Example `data/accounts.txt`:

    ```
    0x123abc...
    0x456def...
    ```

    Example `data/proxies.txt`:

    ```
    http://user:pass@192.168.1.1:8080
    socks5://user2:pass2@192.168.1.2:9090
    ```

## Usage

To run the orchestrator, execute `main.py`:

```bash
python main.py
```

## Extending the Project

-   **New Tasks**: Create new task classes in the `tasks/` directory, inheriting from `BaseTask`.
-   **New Utilities**: Add helper functions or classes to the `utils/` directory.
-   **Web3 Interactions**: Extend `Web3Wrapper` with more specific contract interactions.
-   **Browser Automation**: Add more Playwright automation logic to `StealthBrowser`.

## Contributing

Feel free to fork the repository, make improvements, and submit pull requests.

## License

This project is licensed under the MIT License.
