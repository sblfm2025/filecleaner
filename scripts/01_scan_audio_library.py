import os
import logging
from datetime import datetime
from typing import List, Dict, Any

from src.utils import load_json_config, setup_logger
from src.audio_reader import read_audio_metadata
from src.filename_cleaner import clean_filename
from src.audio_classifier import classify_audio_file
from src.batch_manager import BatchManager
from src.report_writer import write_csv_report, convert_csv_to_xlsx

# Kolom yang akan dimasukkan ke audio_scan_report.csv v3.0
SCAN_COLUMNS = [
    "id", "batch_id", "original_path", "filename", "extension", "file_size_mb",
    "modified_time", "duration_seconds", "duration_readable", "bitrate", "sample_rate",
    "title_tag", "artist_tag", "album_tag", "genre_tag", "year_tag",
    "clean_filename_suggestion", "detected_artist_from_filename",
    "detected_title_from_filename", "parent_folder",
    "media_type", "master_bucket", "suggested_target_folder", "review_folder",
    "confidence_score", "decision", "signals", "warnings", "conflicts",
    "classifier_reason", "status", "notes"
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
    classifier_config = load_json_config("config/classifier_config.json", {})
    
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
            
            # Baca data metadata audio
            meta = read_audio_metadata(filepath)
            filename = os.path.basename(filepath)
            ext = os.path.splitext(filename)[1].lower()
            
            # Dapatkan folder induk relatif terhadap input_dir
            rel_path = os.path.relpath(filepath, input_dir)
            parent_folder = os.path.dirname(rel_path)
            if parent_folder == ".":
                parent_folder = ""

            # Simulasi rename & pembersihan nama file dengan menyertakan tag metadata asli
            cleaned_name, det_artist, det_title, change_reason = clean_filename(
                filename, cleaner_rules, meta["artist_tag"], meta["title_tag"]
            )
            
            # ── KLASIFIKASI MENGGUNAKAN CLASSIFIER MULTI-STAGE v3.0 ─────────
            clf_result = classify_audio_file(
                filename=cleaned_name,
                artist_tag=meta["artist_tag"],
                title_tag=meta["title_tag"],
                genre_tag=meta["genre_tag"],
                duration_seconds=meta["duration_seconds"],
                parent_folder=parent_folder,
                album_tag=meta["album_tag"],
                year_tag=meta["year_tag"],
                config=classifier_config
            )
            
            media_type = clf_result["media_type"]
            master_bucket = clf_result["master_bucket"]
            suggested_target_folder = clf_result["target_folder"]
            review_folder = clf_result["review_folder"]
            confidence_score = clf_result["confidence_score"]
            decision = clf_result["decision"]
            signals = "; ".join(clf_result.get("signals", []))
            warnings_val = "; ".join(clf_result.get("warnings", []))
            conflicts = "; ".join(clf_result.get("conflicts", []))
            classifier_reason = clf_result["reason"]
            
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
                    
            if decision == "NEEDS_REVIEW":
                status = "PERLU_DICEK"
                notes_list.append(f"Confidence rendah: {confidence_score:.0f}/100")
            elif decision == "REVIEW_WITH_SUGGESTION":
                status = "CEK_DENGAN_SARAN"
                notes_list.append(f"Confidence sedang: {confidence_score:.0f}/100 — ada saran folder")
                
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
                "parent_folder": parent_folder,
                "media_type": media_type,
                "master_bucket": master_bucket,
                "suggested_target_folder": suggested_target_folder,
                "review_folder": review_folder,
                "confidence_score": confidence_score,
                "decision": decision,
                "signals": signals,
                "warnings": warnings_val,
                "conflicts": conflicts,
                "classifier_reason": classifier_reason,
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
