import os

AUTH_PASSWORD = "complete777"
BASE_DIR = os.path.dirname(os.path.abspath(os.path.join(os.path.dirname(__file__), "app.py")))

LOTTERY_RED_IMAGE = os.path.join(BASE_DIR, "lottery_red.png")
LOTTERY_GOLD_IMAGE = os.path.join(BASE_DIR, "lottery_gold.png")
LOTTERY_RAINBOW_IMAGE = os.path.join(BASE_DIR, "lottery_rainbow.png")

STORE_CONFIG = {
    "ピーアーク相模大野": {
        "db_path": "database.db",
        "slopachi_table": "ピーアーク相模大野_スロパチ",
        "matomaru_table": "ピーアーク相模大野_まとまる君",
        "map": "p_ark",
    },
    "メガフェイス1180座間店": {
        "db_path": "database.db",
        "slopachi_table": "メガフェイス1180座間店_スロパチ",
        "matomaru_table": None,
        "map": "megaface_zama",
    },
}
