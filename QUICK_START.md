# 🚀 QUICK START GUIDE

## За 5 минут до первого запуска

### Шаг 1: Установка зависимостей (1 мин)
```bash
cd /path/to/crypto_farming_orchestrator
pip install -r requirements.txt
playwright install
```

### Шаг 2: Конфигурация (1 мин)
```bash
# Скопировать .env.example в .env
cp .env.example .env

# Отредактировать .env файл:
# BOT_TOKEN=YOUR_VK_BOT_TOKEN
# PRIVATE_KEYS=0x...key1...,0x...key2...
# INFURA_PROJECT_ID=YOUR_INFURA_ID
```

### Шаг 3: Инициализация шифрования (2 мин - опционально)
```bash
# Сгенерировать и сохранить ключ шифрования
python -c "
from utils.encryption import KeyEncryption
key = KeyEncryption.generate_encryption_key()
KeyEncryption.save_encryption_key(key)
print(f'✅ Ключ сохранен в .keys_encryption_key')
"

# Зашифровать аккаунты
python -c "
from utils.encryption import KeyEncryption
key = KeyEncryption.load_encryption_key()
KeyEncryption.encrypt_accounts_file('data/accounts.txt', key)
print(f'✅ Аккаунты зашифрованы в .encrypted_accounts.json')
"
```

### Шаг 4: Запуск (1 мин)
```bash
python main.py
```

---

## 🔍 Проверка установки

```bash
# Проверить импорты
python -c "
from core.dex_interactions import DEXInteraction
from utils.encryption import KeyEncryption
from utils.transaction_tracker import TransactionTracker
print('✅ Все модули загружены успешно')
"

# Проверить БД для tracking
python -c "
from utils.transaction_tracker import TransactionTracker
tracker = TransactionTracker()
print('✅ Transaction tracker БД инициализирована')
"
```

---

## 💡 Первые примеры

### Пример 1: Получить историю транзакций
```python
from utils.transaction_tracker import TransactionTracker

tracker = TransactionTracker()
history = tracker.get_account_history("0x1234567890...", limit=10)

for tx in history:
    print(f"Type: {tx['tx_type']}, Status: {tx['status']}, Hash: {tx['tx_hash']}")
```

### Пример 2: Шифровать/расшифровать приватный ключ
```python
from utils.encryption import KeyEncryption

key = KeyEncryption.load_encryption_key()

# Зашифровать
encrypted = KeyEncryption.encrypt_private_key("0x123...", key)
print(f"Encrypted: {encrypted[:50]}...")

# Расшифровать
decrypted = KeyEncryption.decrypt_private_key(encrypted, key)
assert decrypted == "0x123..."
```

### Пример 3: Задача с retry логикой
```python
from tasks.swap_task import SwapTask
import asyncio

async def main():
    task = SwapTask(
        private_key="0x...",
        rpc_url="https://mainnet.infura.io/v3/YOUR_ID",
        account_address="0x1234...",
        task_id="swap_demo"
    )
    
    result = await task.run(
        token_in_address="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",  # WETH
        token_out_address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
        amount_in=int(1e18)  # 1 токен
    )
    print(result)

asyncio.run(main())
```

---

## 📊 Структура БД (transaction_history.db)

После первого запуска будут созданы таблицы:

### transactions
```
id          | timestamp      | account_address | task_id    | tx_type
1           | 2024-06-06T... | 0x1234...       | swap_001   | swap
2           | 2024-06-06T... | 0x5678...       | bridge_001 | bridge
```

### task_logs
```
id | timestamp | task_id | account_address | task_type | status
1  | 2024-...  | swap_001| 0x1234...       | swap_task | success
```

---

## 🛠️ Типовые команды

```bash
# Просмотр файлов проекта
tree crypto_farming_orchestrator/

# Проверить синтаксис всех файлов
python -m py_compile core/*.py tasks/*.py utils/*.py

# Запустить транзакции tracker test
python -m utils.transaction_tracker

# Запустить encryption test
python -m utils.encryption

# Генерировать отчет транзакций (CSV)
python -c "
from utils.transaction_tracker import TransactionTracker
tracker = TransactionTracker()
tracker.export_to_csv('report.csv')
print('✅ Отчет создан: report.csv')
"
```

---

## ⚠️ Часто встречающиеся ошибки

### Ошибка: "No module named 'cryptography'"
**Решение:** `pip install cryptography`

### Ошибка: "INFURA_PROJECT_ID not found"
**Решение:** Добавить в .env: `INFURA_PROJECT_ID=your_infura_id`

### Ошибка: "Private key not in plaintext"
**Решение:** Ключи автоматически расшифровываются из .encrypted_accounts.json

### БД-ошибки при параллельных операциях
**Решение:** TransactionTracker использует connection pooling для избежания блокировок

---

## 📈 Что дальше?

1. **Настроить свои задачи** → создать класс наследующий BaseTask
2. **Интегрировать реальный DeFi** → доработать swap_tokens в DEXInteraction
3. **Мониторинг** → использовать transaction_tracker для аналитики
4. **Масштабирование** → параллельное выполнение через TaskOrchestrator

---

**🎉 Вы готовы к разработке крипто-бота!**
