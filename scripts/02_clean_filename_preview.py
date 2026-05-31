import os
import csv
import logging
from typing import List, Dict, Any

from src.utils import load_json_config, setup_logger
from src.filename_cleaner import clean_filename
from src.batch_manager import BatchManager
from src.report_writer import write_csv_report, convert_csv_to_xlsx

# Kolom untuk preview rename
PREVIEW_COLUMNS = [
    "source_path", "old_filename", "new_filename_suggestion", 
    "detected_artist", "detected_title", "change_reason", "safe_to_apply", "notes"
]

def clean_filename_preview(
    batch_id: str,
    input_dir: str = "data/input",
    logs_dir: str = "data/logs"
) -> List[Dict[str, Any]]:
    """
    Membuat simulasi preview pembersihan nama file tanpa menyentuh file fisik.
    Menghasilkan laporan CSV/XLSX.
    """
    logger = logging.getLogger("RADIO_MUSIC_CLEANER")
    logger.info("=== Memulai Preview Pembersihan Nama File ===")
    
    # Muat aturan pembersihan
    cleaner_rules = load_json_config("config/cleaner_rules.json", {})
    
    # Ambil data dari laporan scan jika ada, jika tidak, scan folder secara manual
    scan_report_path = os.path.join(logs_dir, "audio_scan_report.csv")
    file_records: List[Dict[str, Any]] = []
    
    if os.path.exists(scan_report_path):
        logger.info(f"Membaca data scan dari {scan_report_path}")
        try:
            with open(scan_report_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("batch_id") == batch_id:
                        file_records.append(row)
        except Exception as e:
            logger.error(f"Gagal membaca audio_scan_report.csv: {e}")
            
    # Jika laporan scan kosong/tidak ada, lakukan pemindaian dasar
    if not file_records:
        logger.warning("Laporan scan tidak ditemukan atau kosong. Membaca direktori input secara manual.")
        supported_extensions = {".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg", ".wma"}
        for root, _, files in os.walk(input_dir):
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext in supported_extensions:
                    full_path = os.path.join(root, f)
                    file_records.append({
                        "original_path": full_path,
                        "filename": f
                    })
                    
    total_files = len(file_records)
    logger.info(f"Memproses simulasi pembersihan nama untuk {total_files} file...")
    
    preview_records: List[Dict[str, Any]] = []
    batch_mgr = BatchManager(logs_dir)
    
    for row in file_records:
        src_path = row.get("original_path") or row.get("source_path", "")
        old_filename = row.get("filename") or os.path.basename(src_path)
        
        # Bersihkan nama file
        new_name_suggestion, det_artist, det_title, change_reason = clean_filename(old_filename, cleaner_rules)
        
        # Tentukan kelayakan "safe_to_apply"
        safe_to_apply = "YA"
        notes = "Siap untuk rename"
        
        # Cek jika nama file hasil pembersihan sama persis dengan nama lama
        if old_filename.lower() == new_name_suggestion.lower():
            notes = "Nama file sudah bersih, tidak ada perubahan"
        
        # Cek kejelasan
        if not det_artist or not det_title:
            if "-" not in new_name_suggestion:
                safe_to_apply = "YA" # Tetap boleh di-rename meskipun non-musik (seperti jingle)
                notes = "Penamaan non-lagu terdeteksi (tanpa tanda hubung -)"
                
        if not new_name_suggestion or new_name_suggestion.startswith("Cleaned_Audio"):
            safe_to_apply = "TIDAK"
            notes = "Hasil pembersihan nama kosong atau menggunakan fallback default"
            
        preview_row = {
            "source_path": src_path,
            "old_filename": old_filename,
            "new_filename_suggestion": new_name_suggestion,
            "detected_artist": det_artist,
            "detected_title": det_title,
            "change_reason": change_reason,
            "safe_to_apply": safe_to_apply,
            "notes": notes
        }
        
        preview_records.append(preview_row)
        
        # Checkpoint status preview di manifest
        batch_mgr.update_file_status(src_path, stage="preview", status="SUCCESS")
        
    # Tulis laporan preview
    csv_preview_path = os.path.join(logs_dir, "filename_cleaning_preview.csv")
    xlsx_preview_path = os.path.join(logs_dir, "filename_cleaning_preview.xlsx")
    
    write_csv_report(preview_records, csv_preview_path, PREVIEW_COLUMNS)
    convert_csv_to_xlsx(csv_preview_path, xlsx_preview_path)
    
    logger.info(f"=== Preview selesai. Laporan disimpan ke {csv_preview_path} ===")
    return preview_records

if __name__ == "__main__":
    setup_logger()
    clean_filename_preview(batch_id="TEST_BATCH")
