import random
from typing import Dict, Any

def generate_browser_fingerprint() -> Dict[str, Any]:
    """Generates a basic, randomized browser fingerprint for stealth automation."""
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0",
    ]

    screen_resolutions = [
        {"width": 1920, "height": 1080},
        {"width": 1366, "height": 768},
        {"width": 1536, "height": 864},
        {"width": 1440, "height": 900},
        {"width": 1280, "height": 720},
    ]

    languages = [
        "en-US,en;q=0.9",
        "en-GB,en;q=0.9",
        "fr-FR,fr;q=0.9",
        "de-DE,de;q=0.9",
    ]

    return {
        "user_agent": random.choice(user_agents),
        "screen": random.choice(screen_resolutions),
        "accept_language": random.choice(languages),
        "platform": random.choice(["Win32", "MacIntel", "Linux x86_64"]),
        "device_memory": random.choice([2, 4, 8]),
        "hardware_concurrency": random.choice([2, 4, 8, 12]),
    }

if __name__ == "__main__":
    fingerprint = generate_browser_fingerprint()
    print("Generated Browser Fingerprint:")
    for key, value in fingerprint.items():
        print(f"  {key}: {value}")
