import os
import csv
import logging
from typing import List, Dict, Any

from src.utils import setup_logger
from src.audio_reader import read_audio_metadata
from src.report_writer import write_csv_report

# Kolom untuk laporan validasi QA
VALIDATE_COLUMNS = [
    "file_path", "filename", "validation_status", "error_type", 
    "error_message", "recommended_action"
]

def validate_output_library(
    batch_id: str,
    final_output_dir: str = "data/output/RADIO_AUDIO_LIBRARY",
    logs_dir: str = "data/logs"
) -> List[Dict[str, Any]]:
    """
    Melakukan pemeriksaan kualitas (QA) akhir pada library output.
    Memeriksa keterbacaan berkas, panjang path, karakter terlarang, dan kebersihan file ON_AIR_READY.
    """
    logger = logging.getLogger("RADIO_MUSIC_CLEANER")
    logger.info("=== Memulai Validasi Kualitas QA Library Output ===")
    
    # 1. Pastikan folder output final ada
    if not os.path.exists(final_output_dir):
        logger.error(f"Folder library output '{final_output_dir}' tidak ditemukan. Silakan jalankan mode --sort terlebih dahulu.")
        return []
        
    supported_extensions = {".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg", ".wma"}
    audio_files: List[str] = []
    
    for root, _, files in os.walk(final_output_dir):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in supported_extensions:
                audio_files.append(os.path.join(root, f))
                
    total_files = len(audio_files)
    logger.info(f"Ditemukan {total_files} file audio di library output yang akan divalidasi.")
    
    validation_records: List[Dict[str, Any]] = []
    failed_count = 0
    on_air_ready_failed = 0
    path_too_long_count = 0
    
    # 2. Proses validasi per file
    for filepath in audio_files:
        filename = os.path.basename(filepath)
        status = "PASSED"
        err_type = ""
        err_msg = ""
        rec_action = "Aman untuk siaran"
        
        try:
            # A. Cek file kosong (0 byte)
            stat = os.stat(filepath)
            size_bytes = stat.st_size
            if size_bytes == 0:
                status = "FAILED"
                err_type = "FILE_KOSONG"
                err_msg = "Ukuran file adalah 0 byte"
                rec_action = "Hapus berkas dan cari sumber alternatif"
                
            # B. Cek panjang path Windows (peringatan jika mendekati 260)
            if status == "PASSED" and len(filepath) >= 240:
                status = "WARNING"
                err_type = "PATH_TERLALU_PANJANG"
                err_msg = f"Panjang path ({len(filepath)} karakter) berisiko error di Windows (batas 260)"
                rec_action = "Pindahkan ke folder tingkat atas atau perpendek nama artis/judul"
                path_too_long_count += 1
                
            # C. Cek karakter terlarang Windows di nama file
            if status == "PASSED":
                forbidden = ["<", ">", ":", "\"", "/", "\\", "|", "?", "*"]
                found_chars = [c for c in forbidden if c in filename]
                if found_chars:
                    status = "FAILED"
                    err_type = "KARAKTER_TERLARANG"
                    err_msg = f"Mengandung karakter terlarang Windows: {', '.join(found_chars)}"
                    rec_action = "Ubah nama file secara manual untuk menghapus karakter tersebut"
                    
            # D. Cek keterbacaan audio (mutagen reader)
            if status == "PASSED" or status == "WARNING":
                meta = read_audio_metadata(filepath)
                if not meta["is_valid"]:
                    status = "FAILED"
                    err_type = "AUDIO_CORRUPT"
                    err_msg = f"Gagal membaca format audio: {meta['error_message']}"
                    rec_action = "Periksa file secara manual, putar di media player atau encode ulang"
                else:
                    # E. Cek kelayakan folder ON_AIR_READY
                    if "00_ON_AIR_READY" in filepath:
                        on_air_errors = []
                        if not meta["title_tag"]:
                            on_air_errors.append("Title tag kosong")
                        if not meta["artist_tag"]:
                            on_air_errors.append("Artist tag kosong")
                        if meta["duration_seconds"] <= 10.0:
                            on_air_errors.append(f"Durasi terlalu pendek ({meta['duration_readable']})")
                            
                        if on_air_errors:
                            status = "FAILED"
                            err_type = "ON_AIR_READY_INCOMPLETE"
                            err_msg = f"Tidak memenuhi syarat On Air: {'; '.join(on_air_errors)}"
                            rec_action = "Pindahkan file dari ON_AIR_READY ke folder kategori atau lengkapi metadatanya"
                            on_air_ready_failed += 1

        except Exception as e:
            status = "FAILED"
            err_type = "SYSTEM_ERROR"
            err_msg = str(e)
            rec_action = "Periksa perizinan akses file"
            
        if status == "FAILED":
            failed_count += 1
            
        validation_records.append({
            "file_path": filepath,
            "filename": filename,
            "validation_status": status,
            "error_type": err_type,
            "error_message": err_msg,
            "recommended_action": rec_action
        })
        
    # 3. Tulis laporan validasi
    csv_val_path = os.path.join(logs_dir, "output_validation_report.csv")
    write_csv_report(validation_records, csv_val_path, VALIDATE_COLUMNS)
    
    # 4. Buat summary Markdown
    md_val_path = os.path.join(logs_dir, "output_validation_summary.md")
    
    md_content = f"""# Laporan Audit Validasi Kualitas (QA) Library

**ID Batch**: `{batch_id}`  
**Tanggal Audit**: {os.popen('echo %date%').read().strip() if os.name == 'nt' else 'N/A'}  
**Total File Diaudit**: {total_files} file  

---

## Ringkasan Audit Kualitas

* **File Lolos Audit (PASSED)**: {total_files - failed_count - path_too_long_count}  
* **File Peringatan (WARNING)**: {path_too_long_count} (Kemungkinan path panjang Windows)  
* **File Gagal Audit (FAILED)**: {failed_count} (Corrupt, kosong, atau tidak layak On Air)  

### Detail Masalah Spesifik
- Gagal Syarat ON_AIR_READY: {on_air_ready_failed} file  
- Path Terlalu Panjang (>240 char): {path_too_long_count} file  

---

## Panduan Tindakan Operator

1. **Atasi File Gagal (FAILED)**: Silakan buka file `{csv_val_path}` menggunakan Excel untuk menyaring kolom `validation_status` bernilai `FAILED`. Ikuti rekomendasi tindakan pada kolom `recommended_action`.
2. **Koreksi File ON_AIR_READY**: File di folder `00_ON_AIR_READY` yang gagal harus dilengkapi metadatanya menggunakan Mp3tag atau dipindahkan ke subfolder kategori masing-masing.
3. **Pemberesan Path Panjang**: Untuk file berstatus `WARNING` (path terlalu panjang), pastikan aplikasi playlist radio Anda (seperti RadioBoss) tidak bermasalah saat memutar file tersebut. Jika bermasalah, perpendek struktur foldernya.

---
*Laporan Audit Kualitas RADIO_MUSIC_CLEANER.*
"""
    try:
        with open(md_val_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
    except Exception as e:
        logger.error(f"Gagal menulis output_validation_summary.md: {e}")
        
    logger.info(f"=== Validasi selesai. Laporan disimpan ke {csv_val_path} ===")
    return validation_records

if __name__ == "__main__":
    setup_logger()
    validate_output_library(batch_id="TEST_BATCH")
