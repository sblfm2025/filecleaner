import os
import logging
from datetime import datetime
from typing import List, Dict, Any

from src.utils import load_json_config, setup_logger
from src.audio_reader import read_audio_metadata
from src.filename_cleaner import clean_filename
from src.folder_sorter import determine_target_folder
from src.batch_manager import BatchManager
from src.report_writer import write_csv_report, convert_csv_to_xlsx

# Kolom yang akan dimasukkan ke audio_scan_report.csv
SCAN_COLUMNS = [
    "id", "batch_id", "original_path", "filename", "extension", "file_size_mb",
    "modified_time", "duration_seconds", "duration_readable", "bitrate", "sample_rate",
    "title_tag", "artist_tag", "album_tag", "genre_tag", "year_tag",
    "clean_filename_suggestion", "detected_artist_from_filename", 
    "detected_title_from_filename", "suggested_folder", "status", "notes"
]

def scan_audio_library(
    batch_id: str,
    input_dir: str = "data/input",
    logs_dir: str = "data/logs",
    resume: bool = False
) -> List[Dict[str, Any]]:
    """
    Memindai semua file audio di direktori input, membaca metadata,
    dan mencatat data ke laporan scan.
    """
    logger = logging.getLogger("RADIO_MUSIC_CLEANER")
    logger.info(f"=== Memulai Scan Audio Library (Batch: {batch_id}) ===")
    
    # 1. Pastikan folder input ada
    if not os.path.exists(input_dir):
        logger.warning(f"Direktori input '{input_dir}' tidak ditemukan. Membuat direktori baru.")
        os.makedirs(input_dir, exist_ok=True)
        return []
        
    # 2. Muat konfigurasi
    cleaner_rules = load_json_config("config/cleaner_rules.json", {})
    folder_mapping = load_json_config("config/folder_mapping.json", {})
    
    # 3. Inisialisasi Batch Manager
    batch_mgr = BatchManager(logs_dir)
    
    # 4. Temukan semua berkas audio
    supported_extensions = {".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg", ".wma"}
    audio_files: List[str] = []
    
    for root, _, files in os.walk(input_dir):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in supported_extensions:
                audio_files.append(os.path.join(root, f))
                
    total_found = len(audio_files)
    logger.info(f"Ditemukan {total_found} berkas audio di '{input_dir}'")
    
    if total_found == 0:
        logger.info("Scan selesai. Tidak ada berkas audio untuk diproses.")
        return []
        
    scan_records: List[Dict[str, Any]] = []
    processed_count = 0
    
    # 5. Iterasi dan proses masing-masing file
    for filepath in audio_files:
        try:
            stat = os.stat(filepath)
            size_mb = stat.st_size / (1024 * 1024)
            mtime = datetime.fromtimestamp(stat.st_mtime).isoformat()
            
            # Daftarkan file ke manifest
            record = batch_mgr.register_file(filepath, batch_id, size_mb, mtime)
            
            # Jika resume aktif dan file sudah selesai di-scan pada sesi sebelumnya, gunakan data manifest
            if resume and record.get("scan_status") == "SUCCESS":
                logger.debug(f"Resume: Skip scan untuk {filepath}")
                # Load record lama ke list hasil scan
                # Tapi untuk menjaga data laporan terbaru, kita tetap baca ulang atau parsing
                # Agar praktis, kita proses saja karena membaca metadata cepat jika file di lokal
                pass
            
            # Baca data metadata audio
            meta = read_audio_metadata(filepath)
            filename = os.path.basename(filepath)
            ext = os.path.splitext(filename)[1].lower()
            
            # Simulasi rename & pembersihan nama file
            cleaned_name, det_artist, det_title, change_reason = clean_filename(filename, cleaner_rules)
            
            # Tentukan usulan folder sorting
            suggested_folder, sort_reason = determine_target_folder(
                cleaned_name, meta["genre_tag"], det_artist, det_title, folder_mapping
            )
            
            # Tentukan status file
            status = "OK"
            notes_list = []
            
            if not meta["is_valid"]:
                status = "AUDIO_ERROR"
                notes_list.append(meta["error_message"])
            else:
                if not meta["title_tag"]:
                    notes_list.append("Title tag kosong")
                if not meta["artist_tag"]:
                    notes_list.append("Artist tag kosong")
                if change_reason != "Nama file sudah bersih":
                    notes_list.append("Nama file kotor")
                    
            if "90_PERLU_DICEK" in suggested_folder:
                status = "PERLU_DICEK"
                notes_list.append("File terdeteksi ambigu")
                
            notes = "; ".join(notes_list) if notes_list else "Aman"
            
            # Buat record hasil scan
            scan_row = {
                "id": record["file_id"],
                "batch_id": batch_id,
                "original_path": filepath,
                "filename": filename,
                "extension": ext,
                "file_size_mb": round(size_mb, 4),
                "modified_time": mtime,
                "duration_seconds": round(meta["duration_seconds"], 2),
                "duration_readable": meta["duration_readable"],
                "bitrate": meta["bitrate"],
                "sample_rate": meta["sample_rate"],
                "title_tag": meta["title_tag"],
                "artist_tag": meta["artist_tag"],
                "album_tag": meta["album_tag"],
                "genre_tag": meta["genre_tag"],
                "year_tag": meta["year_tag"],
                "clean_filename_suggestion": cleaned_name,
                "detected_artist_from_filename": det_artist,
                "detected_title_from_filename": det_title,
                "suggested_folder": suggested_folder,
                "status": status,
                "notes": notes
            }
            
            scan_records.append(scan_row)
            
            # Perbarui status di manifest batch manager
            batch_mgr.update_file_status(
                filepath, 
                stage="scan", 
                status="SUCCESS" if meta["is_valid"] else "FAILED", 
                error_msg=meta["error_message"]
            )
            
            processed_count += 1
            if processed_count % 50 == 0 or processed_count == total_found:
                logger.info(f"[SCAN] Memproses {processed_count}/{total_found} berkas...")
                
        except Exception as e:
            logger.error(f"Gagal memproses file {filepath} saat scan: {e}")
            batch_mgr.update_file_status(filepath, stage="scan", status="ERROR", error_msg=str(e))
            
    # 6. Tulis laporan hasil scan
    csv_report_path = os.path.join(logs_dir, "audio_scan_report.csv")
    xlsx_report_path = os.path.join(logs_dir, "audio_scan_report.xlsx")
    
    write_csv_report(scan_records, csv_report_path, SCAN_COLUMNS)
    convert_csv_to_xlsx(csv_report_path, xlsx_report_path)
    
    logger.info(f"=== Scan selesai. Laporan disimpan ke {csv_report_path} ===")
    return scan_records

if __name__ == "__main__":
    setup_logger()
    scan_audio_library(batch_id="TEST_BATCH")
