# -*- coding: utf-8 -*-
"""إدارة إعدادات البرنامج (مفتاح API والنموذج المستخدم) - تُحفظ محليًا في config.json"""

import json
import os

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "api_key": "",
    "model": "claude-sonnet-5",
}


def get_config_path():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, CONFIG_FILE)


def load_config():
    path = get_config_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                merged = DEFAULT_CONFIG.copy()
                merged.update(cfg)
                return merged
        except Exception:
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()


def save_config(cfg):
    path = get_config_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
