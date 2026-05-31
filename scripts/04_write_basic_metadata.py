import os
import csv
import logging
from typing import List, Dict, Any

from src.utils import load_json_config, setup_logger
from src.audio_reader import read_audio_metadata
from src.metadata_writer import write_basic_metadata
from src.batch_manager import BatchManager
from src.report_writer import write_csv_report, convert_csv_to_xlsx

# Kolom untuk laporan metadata
METADATA_COLUMNS = [
    "file_path", "old_title", "new_title", "old_artist", "new_artist",
    "old_album", "new_album", "old_genre", "new_genre", "status", "notes"
]

def write_basic_metadata_to_batch(
    batch_id: str,
    logs_dir: str = "data/logs",
    resume: bool = False
) -> List[Dict[str, Any]]:
    """
    Menulis metadata dasar (Artist & Title) pada file audio hasil salinan yang tag-nya kosong.
    Membaca data manifest untuk menemukan file yang sukses disalin/di-rename.
    """
    logger = logging.getLogger("RADIO_MUSIC_CLEANER")
    logger.info("=== Memulai Penulisan Metadata Dasar ===")
    
    # 1. Muat konfigurasi default metadata
    meta_defaults = load_json_config("config/metadata_defaults.json", {})
    
    # 2. Inisialisasi Batch Manager
    batch_mgr = BatchManager(logs_dir)
    batch_records = batch_mgr.get_all_records_for_batch(batch_id)
    
    if not batch_records:
        # Fallback membaca file applied jika manifest kosong
        logger.warning("Data manifest batch tidak ditemukan. Membaca dari filename_cleaning_applied.csv...")
        applied_report_path = os.path.join(logs_dir, "filename_cleaning_applied.csv")
        if os.path.exists(applied_report_path):
            try:
                with open(applied_report_path, mode='r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row.get("copy_status") == "SUCCESS" and row.get("target_path"):
                            batch_records.append({
                                "source_path": row.get("source_path"),
                                "target_path": row.get("target_path"),
                                "rename_status": "SUCCESS",
                                "metadata_status": "PENDING"
                            })
            except Exception as e:
                logger.error(f"Gagal membaca filename_cleaning_applied.csv: {e}")

    # Saring file yang siap ditulis metadata (yang sukses di-copy/rename)
    target_records = [r for r in batch_records if r.get("rename_status") == "SUCCESS" and r.get("target_path")]
    
    if not target_records:
        logger.error("Tidak ada file audio yang terdeteksi sukses disalin untuk ditulis metadatanya.")
        return []
        
    logger.info(f"Ditemukan {len(target_records)} file audio hasil salinan yang siap diproses metadatanya.")
    
    metadata_records: List[Dict[str, Any]] = []
    processed_count = 0
    
    # Muat juga info scan untuk mendapatkan detected_artist dan detected_title
    scan_report_path = os.path.join(logs_dir, "audio_scan_report.csv")
    scan_data_map: Dict[str, Dict[str, Any]] = {}
    
    if os.path.exists(scan_report_path):
        try:
            with open(scan_report_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    scan_data_map[row["original_path"]] = row
        except Exception as e:
            logger.error(f"Gagal memuat peta data scan: {e}")

    # 3. Iterasi penulisan metadata
    for row in target_records:
        src_path = row.get("source_path")
        target_path = row.get("target_path")
        
        # Validasi path fisik
        if not target_path or not os.path.exists(target_path):
            logger.warning(f"File target tidak ditemukan di disk: {target_path}")
            continue
            
        # Cek resume
        if resume and row.get("metadata_status") == "SUCCESS":
            logger.info(f"Resume: Skip metadata untuk {os.path.basename(target_path)}")
            # Masukkan info dummy/lama untuk konsistensi laporan
            metadata_records.append({
                "file_path": target_path,
                "old_title": "", "new_title": "",
                "old_artist": "", "new_artist": "",
                "old_album": "", "new_album": "",
                "old_genre": "", "new_genre": "",
                "status": "SKIPPED",
                "notes": "Dilewati karena sudah selesai pada sesi sebelumnya (Resume)"
            })
            continue

        # Ambil usulan Artist & Title hasil deteksi scan
        scan_info = scan_data_map.get(src_path, {})
        det_artist = scan_info.get("detected_artist_from_filename", "")
        det_title = scan_info.get("detected_title_from_filename", "")
        suggested_folder = scan_info.get("suggested_folder", "")
        
        # Cari rekomendasi genre berdasarkan usulan folder
        suggested_genre = ""
        if suggested_folder:
            if "Musik_Lokal_Daerah" in suggested_folder or "01_MUSIK_LOKAL_DAERAH" in suggested_folder:
                suggested_genre = meta_defaults.get("default_genre_local", "Musik Lokal Daerah")
            elif "Musik_Indonesia" in suggested_folder or "02_MUSIK_INDONESIA" in suggested_folder:
                suggested_genre = meta_defaults.get("default_genre_music", "Musik")
            elif "Jingle" in suggested_folder or "Jingle_Station_ID" in suggested_folder:
                suggested_genre = meta_defaults.get("default_genre_jingle", "Jingle")
            elif "Bumper" in suggested_folder or "Bumper_Program" in suggested_folder:
                suggested_genre = meta_defaults.get("default_genre_bumper", "Bumper")
            elif "Iklan" in suggested_folder:
                suggested_genre = meta_defaults.get("default_genre_iklan", "Iklan")
            elif "ILM" in suggested_folder:
                suggested_genre = meta_defaults.get("default_genre_ilm", "Iklan Layanan Masyarakat")
            elif "PROGRAM_REKAMAN" in suggested_folder or "05_PROGRAM_REKAMAN" in suggested_folder:
                suggested_genre = meta_defaults.get("default_genre_program", "Program Rekaman")

        # Baca metadata lama sebelum ditulis (untuk laporan perbandingan)
        old_meta = read_audio_metadata(target_path)
        
        # Tulis metadata baru secara aman
        status, notes = write_basic_metadata(
            target_path,
            artist=det_artist,
            title=det_title,
            defaults=meta_defaults,
            suggested_genre=suggested_genre
        )
        
        # Baca kembali metadata yang baru ditulis
        new_meta = read_audio_metadata(target_path)
        
        metadata_row = {
            "file_path": target_path,
            "old_title": old_meta.get("title_tag", ""),
            "new_title": new_meta.get("title_tag", ""),
            "old_artist": old_meta.get("artist_tag", ""),
            "new_artist": new_meta.get("artist_tag", ""),
            "old_album": old_meta.get("album_tag", ""),
            "new_album": new_meta.get("album_tag", ""),
            "old_genre": old_meta.get("genre_tag", ""),
            "new_genre": new_meta.get("genre_tag", ""),
            "status": status,
            "notes": notes
        }
        
        metadata_records.append(metadata_row)
        
        # Checkpoint status metadata di manifest
        batch_mgr.update_file_status(src_path, stage="metadata", status=status, error_msg="" if status == "SUCCESS" else notes)
        
        processed_count += 1
        if processed_count % 50 == 0 or processed_count == len(target_records):
            logger.info(f"[METADATA] Menulis tag {processed_count}/{len(target_records)} file...")
            
    # Tulis laporan metadata
    csv_metadata_path = os.path.join(logs_dir, "metadata_write_report.csv")
    xlsx_metadata_path = os.path.join(logs_dir, "metadata_write_report.xlsx")
    
    write_csv_report(metadata_records, csv_metadata_path, METADATA_COLUMNS)
    convert_csv_to_xlsx(csv_metadata_path, xlsx_metadata_path)
    
    logger.info(f"=== Penulisan metadata selesai. Laporan disimpan ke {csv_metadata_path} ===")
    return metadata_records

if __name__ == "__main__":
    setup_logger()
    write_basic_metadata_to_batch(batch_id="TEST_BATCH")
