"""
src/operation_log.py — Modul Pencatat Log Operasi Keselamatan Berkas v4.0
========================================================================
Mencatat setiap tindakan modifikasi fisik berkas lagu (salin, rename, tulis tag)
secara atomik ke dalam berkas audit log transparan data/logs/operation_log.csv.

Keamanan Data: Tidak ada perubahan fisik yang boleh dieksekusi tanpa pencatatan log.
"""

import os
import csv
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from src.report_writer import write_csv_report

logger = logging.getLogger("RADIO_MUSIC_CLEANER")

# Kolom audit log operasi stasiun radio v4.0
OPERATION_LOG_COLUMNS = [
    "operation_id", "timestamp", "file_id", "operation_type", 
    "source_path", "target_path", "old_filename", "new_filename", 
    "old_tags_json", "new_tags_json", "decision_source", 
    "confidence_score", "operator", "rollback_available"
]


def log_operation(
    logs_dir: str,
    file_id: str,
    operation_type: str,
    source_path: str,
    target_path: str,
    old_filename: str,
    new_filename: str,
    old_tags: Dict[str, Any],
    new_tags: Dict[str, Any],
    decision_source: str,
    confidence_score: float,
    operator: str = "SYSTEM_CLASSIFIER",
    rollback_available: str = "YES"
) -> Optional[str]:
    """
    Mencatat entri operasi baru ke dalam log audit operation_log.csv stasiun radio.
    Mengembalikan operation_id yang unik jika berhasil, atau None.
    """
    os.makedirs(logs_dir, exist_ok=True)
    csv_path = os.path.join(logs_dir, "operation_log.csv")
    
    # 1. Buat ID operasi unik berbasis waktu
    timestamp = datetime.now().isoformat()
    op_counter = 1
    
    # Jika berkas log sudah ada, hitung jumlah baris untuk membuat counter ID unik
    if os.path.exists(csv_path):
        try:
            with open(csv_path, mode='r', encoding='utf-8') as f:
                op_counter = sum(1 for _ in f)
        except Exception:
            pass
            
    operation_id = f"OP-{op_counter:06d}-{datetime.now().strftime('%m%d%H%M%S')}"

    # 2. Serialize tags dictionary ke string JSON
    old_tags_str = json.dumps(old_tags, ensure_ascii=False) if old_tags else "{}"
    new_tags_str = json.dumps(new_tags, ensure_ascii=False) if new_tags else "{}"

    # 3. Susun data entri log
    log_row = {
        "operation_id": operation_id,
        "timestamp": timestamp,
        "file_id": file_id,
        "operation_type": operation_type,
        "source_path": os.path.abspath(source_path) if source_path else "",
        "target_path": os.path.abspath(target_path) if target_path else "",
        "old_filename": old_filename,
        "new_filename": new_filename,
        "old_tags_json": old_tags_str,
        "new_tags_json": new_tags_str,
        "decision_source": decision_source,
        "confidence_score": round(confidence_score, 1),
        "operator": operator,
        "rollback_available": rollback_available
    }

    # 4. Tulis entri secara append ke berkas CSV
    write_header = not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0
    
    try:
        with open(csv_path, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=OPERATION_LOG_COLUMNS)
            if write_header:
                writer.writeheader()
            writer.writerow(log_row)
            
        logger.debug(f"[OP_LOG] Sukses mencatat operasi {operation_id} untuk {new_filename}")
        return operation_id
    except Exception as e:
        logger.error(f"[OP_LOG] Gagal menulis ke log operasi: {e}")
        
    return None
