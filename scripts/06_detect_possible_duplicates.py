import os
import csv
import logging
from typing import List, Dict, Any

from src.utils import load_json_config, setup_logger
from src.audio_reader import read_audio_metadata
from src.duplicate_detector import detect_duplicates_in_list
from src.safe_file_ops import safe_copy_file
from src.report_writer import write_csv_report, convert_csv_to_xlsx

# Kolom untuk laporan duplikat
DUPLICATE_COLUMNS = [
    "group_id", "file_path", "filename", "artist", "title", 
    "duration_seconds", "file_size_mb", "similarity_score", 
    "duplicate_reason", "recommended_action"
]

def detect_possible_duplicates(
    batch_id: str,
    final_output_dir: str = "data/output/RADIO_AUDIO_LIBRARY",
    logs_dir: str = "data/logs",
    duplicate_dest_dir: str = "data/duplikat_diduga"
) -> List[Dict[str, Any]]:
    """
    Mendeteksi file duplikat di dalam library output final,
    membuat laporan duplikat, dan menyalin file tersangka ke folder khusus.
    """
    logger = logging.getLogger("RADIO_MUSIC_CLEANER")
    logger.info("=== Memulai Deteksi Dugaan Duplikat Audio ===")
    
    # 1. Pastikan folder duplikat tujuan ada
    os.makedirs(duplicate_dest_dir, exist_ok=True)
    
    # 2. Temukan semua berkas audio di output library final
    supported_extensions = {".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg", ".wma"}
    audio_files: List[str] = []
    
    for root, _, files in os.walk(final_output_dir):
        # Lewati folder duplikat diduga jika berada di dalam struktur yang sama
        if "91_DUPLIKAT_DIDUGA" in root or "duplikat_diduga" in root:
            continue
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in supported_extensions:
                audio_files.append(os.path.join(root, f))
                
    total_files = len(audio_files)
    logger.info(f"Membaca metadata untuk {total_files} file di output library untuk deteksi duplikat...")
    
    if total_files <= 1:
        logger.info("Jumlah berkas terlalu sedikit untuk analisis duplikat.")
        return []
        
    # 3. Kumpulkan metadata dari disk
    file_records: List[Dict[str, Any]] = []
    processed = 0
    
    for filepath in audio_files:
        try:
            stat = os.stat(filepath)
            size_mb = stat.st_size / (1024 * 1024)
            meta = read_audio_metadata(filepath)
            
            file_records.append({
                "source_path": filepath,
                "file_size_mb": size_mb,
                "duration_seconds": meta["duration_seconds"],
                "artist_tag": meta["artist_tag"],
                "title_tag": meta["title_tag"]
            })
            
            processed += 1
            if processed % 100 == 0 or processed == total_files:
                logger.info(f"Membaca metadata: {processed}/{total_files} file...")
        except Exception as e:
            logger.error(f"Gagal membaca metadata file {filepath} saat cek duplikat: {e}")

    # 4. Deteksi duplikat menggunakan modul detektor
    logger.info("Menganalisis kemiripan data...")
    duplicates_report = detect_duplicates_in_list(file_records)
    
    total_duplicates = len(duplicates_report)
    logger.info(f"Terdeteksi {total_duplicates} file terduga duplikat.")
    
    if total_duplicates == 0:
        logger.info("Tidak ada dugaan duplikat terdeteksi.")
        
        # Tulis laporan kosong agar file CSV tetap terbentuk
        csv_dup_path = os.path.join(logs_dir, "possible_duplicates_report.csv")
        write_csv_report([], csv_dup_path, DUPLICATE_COLUMNS)
        return []
        
    # 5. Salin file tersangka ke folder duplikat diduga (tanpa menghapus file asli)
    logger.info(f"Menyalin file terduga duplikat ke folder '{duplicate_dest_dir}' untuk audit manual...")
    
    for row in duplicates_report:
        filepath = row["file_path"]
        filename = row["filename"]
        group_id = row["group_id"]
        
        # Beri prefix ID Grup pada file agar operator tahu file mana saja yang satu grup
        prefixed_filename = f"{group_id}_{filename}"
        
        # Terapkan penyalinan aman ke folder review duplikat
        safe_copy_file(filepath, duplicate_dest_dir, prefixed_filename)
        
    # 6. Tulis laporan duplikat
    csv_dup_path = os.path.join(logs_dir, "possible_duplicates_report.csv")
    xlsx_dup_path = os.path.join(logs_dir, "possible_duplicates_report.xlsx")
    
    write_csv_report(duplicates_report, csv_dup_path, DUPLICATE_COLUMNS)
    convert_csv_to_xlsx(csv_dup_path, xlsx_dup_path)
    
    logger.info(f"=== Deteksi duplikat selesai. Laporan disimpan ke {csv_dup_path} ===")
    return duplicates_report

if __name__ == "__main__":
    setup_logger()
    detect_possible_duplicates(batch_id="TEST_BATCH")
