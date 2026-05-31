"""
src/rollback_manager.py — Modul Manajer Pemulihan Keselamatan Berkas v4.0
==========================================================================
Mengelola pencatatan draf kondisi berkas sebelum modifikasi fisik
dan menyediakan utilitas pemulihan (rollback) instan berkas ke kondisi semula.

Pagar Pengaman:
  - Rollback hanya memodifikasi berkas di folder output (output_batch atau master).
  - Tidak akan pernah menyentuh berkas di direktori input asli Anda.
"""

import os
import csv
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

from src.audio_reader import read_audio_metadata
from src.metadata_writer import write_basic_metadata
from src.utils import load_json_config

logger = logging.getLogger("RADIO_MUSIC_CLEANER")

# Kolom manifest rollback stasiun radio v4.0
ROLLBACK_MANIFEST_COLUMNS = [
    "operation_id", "file_id", "current_path", "original_source_path", 
    "original_filename", "original_tags_json", "timestamp", "status"
]


def write_to_rollback_manifest(
    logs_dir: str,
    operation_id: str,
    file_id: str,
    current_path: str,
    original_source_path: str,
    original_filename: str,
    original_tags: Dict[str, Any]
) -> bool:
    """
    Menulis entri pemulihan baru ke dalam berkas manifest rollback_manifest.csv.
    """
    os.makedirs(logs_dir, exist_ok=True)
    csv_path = os.path.join(logs_dir, "rollback_manifest.csv")
    
    tags_str = json.dumps(original_tags, ensure_ascii=False) if original_tags else "{}"
    timestamp = datetime.now().isoformat()

    row = {
        "operation_id": operation_id,
        "file_id": file_id,
        "current_path": os.path.abspath(current_path) if current_path else "",
        "original_source_path": os.path.abspath(original_source_path) if original_source_path else "",
        "original_filename": original_filename,
        "original_tags_json": tags_str,
        "timestamp": timestamp,
        "status": "ACTIVE"
    }

    write_header = not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0

    try:
        with open(csv_path, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=ROLLBACK_MANIFEST_COLUMNS)
            if write_header:
                writer.writeheader()
            writer.writerow(row)
        logger.debug(f"[ROLLBACK] Sukses mencatat manifest pemulihan untuk operasi: {operation_id}")
        return True
    except Exception as e:
        logger.error(f"[ROLLBACK] Gagal menulis ke manifest rollback: {e}")
        
    return False


def execute_rollback_for_file(
    logs_dir: str,
    operation_id: str
) -> Tuple[bool, str]:
    """
    Memicu proses pemulihan keselamatan fisik dan metadata berkas stasiun radio
    berdasarkan Recording ID operasi.
    
    Return:
        Tuple (success, message_status)
    """
    csv_path = os.path.join(logs_dir, "rollback_manifest.csv")
    if not os.path.exists(csv_path):
        return False, "Berkas manifest rollback tidak ditemukan."

    # 1. Baca manifest untuk mencari entri operasi yang cocok
    matched_row: Optional[Dict[str, str]] = None
    all_rows: List[Dict[str, str]] = []

    try:
        with open(csv_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for r in reader:
                if r.get("operation_id") == operation_id:
                    matched_row = r
                all_rows.append(r)
    except Exception as e:
        return False, f"Gagal membaca manifest rollback: {e}"

    if not matched_row:
        return False, f"Operasi pemulihan '{operation_id}' tidak terdaftar di manifest."

    if matched_row.get("status") == "ROLLED_BACK":
        return False, f"Operasi '{operation_id}' sudah pernah di-rollback sebelumnya."

    # Parameter pemulihan
    current_path = matched_row.get("current_path", "")
    original_source_path = matched_row.get("original_source_path", "")
    original_filename = matched_row.get("original_filename", "")
    original_tags_str = matched_row.get("original_tags_json", "{}")

    # Pagar Pengaman: Jangan pernah memodifikasi file di folder input asli!
    # Pastikan current_path berada di folder output atau output_batch
    abs_curr = os.path.abspath(current_path)
    if "data\\input" in abs_curr.lower():
        return False, "Pagar Pengaman: Dilarang memodifikasi berkas di folder input stasiun radio."

    if not os.path.exists(current_path):
        return False, f"Berkas fisik saat ini tidak ditemukan di disk: {current_path}"

    # 2. Eksekusi pemulihan tag metadata lama
    try:
        old_tags = json.loads(original_tags_str)
    except Exception:
        old_tags = {}

    logger.info(f"[ROLLBACK] Memulihkan tag metadata untuk berkas: {current_path}")
    
    # Kosongkan tag terlebih dahulu, lalu timpa dengan tag asli
    meta_defaults = load_json_config("config/metadata_defaults.json", {})
    write_status, write_notes = write_basic_metadata(
        current_path,
        artist=old_tags.get("artist_tag", ""),
        title=old_tags.get("title_tag", ""),
        defaults=meta_defaults,
        suggested_genre=old_tags.get("genre_tag", "")
    )

    if write_status != "SUCCESS":
        return False, f"Gagal memulihkan tag metadata asli: {write_notes}"

    # 3. Eksekusi pemulihan nama file fisik
    # Pindahkan kembali file ke target original_source_path ( folder batch lama / nama file asli )
    target_dir = os.path.dirname(original_source_path)
    
    # Jika folder batch asalnya sudah terhapus, buat kembali secara aman
    os.makedirs(target_dir, exist_ok=True)

    logger.info(f"[ROLLBACK] Memulihkan nama berkas ke: {original_source_path}")
    
    try:
        # Pindahkan fisik file di disk
        if os.path.exists(original_source_path):
            # Jika file original sudah ada (misalnya duplikasi), hapus yang baru agar tidak tabrakan
            os.remove(current_path)
            logger.warning("[ROLLBACK] Berkas original sudah ada di tujuan, menghapus berkas modifikasi.")
        else:
            os.rename(current_path, original_source_path)
    except Exception as ex:
        return False, f"Gagal memindahkan fisik berkas: {ex}"

    # 4. Perbarui status manifest di memori dan tulis kembali ke disk
    for r in all_rows:
        if r.get("operation_id") == operation_id:
            r["status"] = "ROLLED_BACK"

    try:
        with open(csv_path, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=ROLLBACK_MANIFEST_COLUMNS)
            writer.writeheader()
            writer.writerows(all_rows)
    except Exception as e:
        logger.error(f"[ROLLBACK] Gagal memperbarui manifest di disk: {e}")

    logger.info(f"[ROLLBACK] Operasi pemulihan {operation_id} berhasil dituntaskan dengan sukses!")
    return True, f"Sukses memulihkan berkas {original_filename} ke kondisi semula."
