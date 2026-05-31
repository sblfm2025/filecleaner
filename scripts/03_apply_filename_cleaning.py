import os
import csv
import logging
from typing import List, Dict, Any

from src.utils import load_json_config, setup_logger
from src.safe_file_ops import safe_copy_file
from src.batch_manager import BatchManager
from src.report_writer import write_csv_report

APPLY_COLUMNS = [
    "source_path", "target_path", "old_filename", "new_filename", 
    "copy_status", "rename_status", "notes"
]

def apply_filename_cleaning(
    batch_id: str,
    output_batch_dir: str = "data/output_batch",
    logs_dir: str = "data/logs",
    resume: bool = False
) -> List[Dict[str, Any]]:
    """
    Menyalin file asli dari input ke folder output batch sekaligus
    menerapkan pergantian nama file baru yang bersih.
    """
    logger = logging.getLogger("RADIO_MUSIC_CLEANER")
    logger.info(f"=== Menerapkan Pembersihan Nama File (Salin & Rename) ===")
    
    # 1. Pastikan folder output batch ada
    os.makedirs(output_batch_dir, exist_ok=True)
    
    # 2. Muat laporan preview rename
    preview_report_path = os.path.join(logs_dir, "filename_cleaning_preview.csv")
    preview_records: List[Dict[str, Any]] = []
    
    if os.path.exists(preview_report_path):
        try:
            with open(preview_report_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                preview_records = list(reader)
        except Exception as e:
            logger.error(f"Gagal membaca filename_cleaning_preview.csv: {e}")
            
    if not preview_records:
        logger.error("Laporan preview rename kosong atau tidak ditemukan! Silakan jalankan mode --preview terlebih dahulu.")
        return []
        
    # 3. Inisialisasi Batch Manager
    batch_mgr = BatchManager(logs_dir)
    
    applied_records: List[Dict[str, Any]] = []
    total_files = len(preview_records)
    processed_count = 0
    
    logger.info(f"Memulai penyalinan dan penggantian nama untuk {total_files} file...")
    
    # 4. Proses penyalinan
    for row in preview_records:
        src_path = row.get("source_path", "")
        old_filename = row.get("old_filename", "")
        new_filename = row.get("new_filename_suggestion", "")
        safe_to_apply = row.get("safe_to_apply", "YA")
        
        # Validasi awal
        if not src_path or not os.path.exists(src_path):
            logger.warning(f"File sumber tidak ditemukan: {src_path}")
            continue
            
        # Cek manifest untuk resume
        manifest_record = batch_mgr.get_file_record(src_path)
        if resume and manifest_record and manifest_record.get("rename_status") == "SUCCESS":
            logger.info(f"Resume: Skip file {old_filename} (Sudah diproses)")
            # Masukkan info ke laporan applied untuk konsistensi
            applied_records.append({
                "source_path": src_path,
                "target_path": manifest_record.get("target_path", ""),
                "old_filename": old_filename,
                "new_filename": os.path.basename(manifest_record.get("target_path", "")),
                "copy_status": "SUCCESS",
                "rename_status": "SUCCESS",
                "notes": "Dilewati karena sudah selesai pada sesi sebelumnya (Resume)"
            })
            continue

        if safe_to_apply != "YA":
            logger.info(f"File {old_filename} ditandai TIDAK aman untuk rename otomatis. Lewati.")
            applied_records.append({
                "source_path": src_path,
                "target_path": "",
                "old_filename": old_filename,
                "new_filename": new_filename,
                "copy_status": "SKIPPED",
                "rename_status": "SKIPPED",
                "notes": f"Ditandai tidak aman di preview: {row.get('notes', '')}"
            })
            batch_mgr.update_file_status(src_path, stage="rename", status="SKIPPED", error_msg="Ditandai tidak aman di preview")
            continue
            
        # Panggil safe_copy_file untuk melakukan copy & rename aman
        actual_target_path, copy_res = safe_copy_file(src_path, output_batch_dir, new_filename)
        
        if copy_res == "SUCCESS":
            logger.debug(f"Sukses menyalin & rename: {old_filename} -> {new_filename}")
            applied_row = {
                "source_path": src_path,
                "target_path": actual_target_path,
                "old_filename": old_filename,
                "new_filename": os.path.basename(actual_target_path),
                "copy_status": "SUCCESS",
                "rename_status": "SUCCESS",
                "notes": f"Sukses disalin ke {output_batch_dir}"
            }
            batch_mgr.update_file_status(src_path, stage="rename", status="SUCCESS", target_path=actual_target_path)
        else:
            logger.error(f"Gagal menyalin {old_filename}: {copy_res}")
            applied_row = {
                "source_path": src_path,
                "target_path": "",
                "old_filename": old_filename,
                "new_filename": new_filename,
                "copy_status": "FAILED",
                "rename_status": "FAILED",
                "notes": copy_res
            }
            batch_mgr.update_file_status(src_path, stage="rename", status="FAILED", error_msg=copy_res)
            
        applied_records.append(applied_row)
        
        processed_count += 1
        if processed_count % 50 == 0 or processed_count == total_files:
            logger.info(f"[RENAME] Menyalin & rename {processed_count}/{total_files} berkas...")
            
    # Tulis laporan applied
    csv_applied_path = os.path.join(logs_dir, "filename_cleaning_applied.csv")
    write_csv_report(applied_records, csv_applied_path, APPLY_COLUMNS)
    
    logger.info(f"=== Penerapan rename selesai. Laporan disimpan ke {csv_applied_path} ===")
    return applied_records

if __name__ == "__main__":
    setup_logger()
    apply_filename_cleaning(batch_id="TEST_BATCH")
