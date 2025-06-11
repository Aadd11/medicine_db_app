import json
from pathlib import Path

CONFIG_FILE = Path.home() / '.medicine_db_config.json'

def save_db_config(db_url: str):
    with open(CONFIG_FILE, 'w') as f:
        json.dump({'db_url': db_url}, f)

def load_db_config() -> str | None:
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f).get('db_url')
    return None
