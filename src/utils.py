import os
import json
import logging
from typing import Any, Dict

def load_json_config(file_path: str, default_val: Any = None) -> Any:
    """
    Membaca berkas konfigurasi JSON secara aman.
    Jika berkas tidak ditemukan atau JSON tidak valid, akan menampilkan peringatan dan menggunakan nilai default.
    """
    if not os.path.exists(file_path):
        logging.warning(f"Berkas konfigurasi tidak ditemukan di {file_path}. Menggunakan nilai default.")
        return default_val
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logging.error(f"Format JSON tidak valid di {file_path}: {e}. Menggunakan nilai default.")
        return default_val
    except Exception as e:
        logging.error(f"Gagal membaca konfigurasi {file_path}: {e}. Menggunakan nilai default.")
        return default_val

def setup_logger(log_dir: str = "data/logs") -> logging.Logger:
    """
    Mengatur logger terpadu untuk menyimpan log ke berkas dan menampilkan informasi ke konsol.
    """
    os.makedirs(log_dir, exist_ok=True)
    logger = logging.getLogger("RADIO_MUSIC_CLEANER")
    
    # Hindari duplikasi handler jika sudah diatur sebelumnya
    if logger.handlers:
        return logger
        
    logger.setLevel(logging.DEBUG)
    
    # Handler untuk file log rinci
    log_file = os.path.join(log_dir, "app.log")
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d]: %(message)s")
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Handler untuk konsol (hanya menampilkan level INFO ke atas dengan ringkas)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter("[%(levelname)s] %(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    return logger

import importlib.util
import sys

def import_module_by_path(module_name: str, file_path: str) -> Any:
    """
    Mengimpor modul secara dinamis dari path berkas fisik.
    Digunakan untuk modul yang diawali angka agar tidak melanggar parser Python.
    """
    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Tidak dapat membuat spec modul untuk {file_path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        logging.error(f"Gagal mengimpor modul {module_name} secara dinamis dari {file_path}: {e}")
        raise e
