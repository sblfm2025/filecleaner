"""
scripts/09_classify_and_report.py — Utilitas Audit Klasifikasi Audio Standalone v3.0
=====================================================================================
Memindai folder audio dan menjalankan klasifikasi confidence-based v3.0 untuk
menghasilkan laporan audit klasifikasi detail (classification_report.csv/xlsx).
Sangat aman: tidak menyalin, tidak memindahkan, dan tidak merubah tag file fisik.

Penggunaan:
    python scripts/09_classify_and_report.py --input data/input --output-dir data/logs
"""

import os
import sys
import csv
import argparse
import logging
from datetime import datetime
from typing import List, Dict, Any

# Pastikan root workspace masuk sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils import setup_logger, load_json_config
from src.audio_reader import read_audio_metadata
from src.filename_cleaner import clean_filename
from src.audio_classifier import classify_audio_file
from src.report_writer import write_csv_report, convert_csv_to_xlsx

logger = logging.getLogger("RADIO_MUSIC_CLEANER")

# Kolom laporan audit klasifikasi standalone v3.0
CLASSIFY_COLUMNS = [
    "filepath", "filename", "media_type", "master_bucket",
    "suggested_target_folder", "review_folder", "confidence_score",
    "decision", "signals", "warnings", "conflicts", "reason"
]


def run_classification_audit(
    input_dir: str = "data/input",
    logs_dir: str = "data/logs"
) -> List[Dict[str, Any]]:
    """
    Menjalankan audit klasifikasi pada seluruh file audio di direktori input.
    """
    logger.info("======================================================================")
    logger.info("      MEMULAI AUDIT KLASIFIKASI AUDIO STANDALONE v3.0")
    logger.info("======================================================================")
    
    if not os.path.exists(input_dir):
        logger.error(f"Direktori input '{input_dir}' tidak ditemukan.")
        return []

    os.makedirs(logs_dir, exist_ok=True)

    # Muat konfigurasi pendukung
    cleaner_rules = load_json_config("config/cleaner_rules.json", {})

    # Cari file audio
    supported_extensions = {".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg", ".wma"}
    audio_files: List[str] = []
    
    for root, _, files in os.walk(input_dir):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in supported_extensions:
                audio_files.append(os.path.join(root, f))

    total_files = len(audio_files)
    logger.info(f"Ditemukan {total_files} berkas audio untuk di-audit klasifikasinya.")

    if total_files == 0:
        logger.info("Audit selesai: Tidak ada berkas audio ditemukan.")
        return []

    classification_records: List[Dict[str, Any]] = []
    
    # Statistik counter
    stats = {
        "AUTO_SORT": 0,
        "REVIEW_WITH_SUGGESTION": 0,
        "NEEDS_REVIEW": 0,
        "REJECT_BAD_AUDIO": 0
    }
    total_confidence = 0.0

    for idx, filepath in enumerate(audio_files, 1):
        try:
            # Baca metadata dasar
            meta = read_audio_metadata(filepath)
            filename = os.path.basename(filepath)
            
            # Parent folder hint
            rel_path = os.path.relpath(filepath, input_dir)
            parent_folder = os.path.dirname(rel_path)
            if parent_folder == ".":
                parent_folder = ""

            # Dapatkan usulan nama bersih untuk pencocokan yang lebih akurat
            cleaned_name, _, _, _ = clean_filename(
                filename, cleaner_rules, meta["artist_tag"], meta["title_tag"]
            )

            # Jalankan Classifier Multi-Stage v3.0
            clf = classify_audio_file(
                filename=cleaned_name,
                source_path=filepath,
                parent_folder=parent_folder,
                duration_seconds=meta["duration_seconds"],
                genre_tag=meta["genre_tag"],
                artist_tag=meta["artist_tag"],
                title_tag=meta["title_tag"],
                album_tag=meta["album_tag"],
                year_tag=meta["year_tag"]
            )

            decision = clf["decision"]
            confidence = clf["confidence_score"]
            
            # Update statistik
            stats[decision] = stats.get(decision, 0) + 1
            total_confidence += confidence

            record = {
                "filepath": filepath,
                "filename": filename,
                "media_type": clf["media_type"],
                "master_bucket": clf["master_bucket"],
                "suggested_target_folder": clf["target_folder"],
                "review_folder": clf["review_folder"],
                "confidence_score": confidence,
                "decision": decision,
                "signals": "; ".join(clf.get("signals", [])),
                "warnings": "; ".join(clf.get("warnings", [])),
                "conflicts": "; ".join(clf.get("conflicts", [])),
                "reason": clf["reason"]
            }
            classification_records.append(record)

            if idx % 50 == 0 or idx == total_files:
                logger.info(f"[AUDIT] Memproses {idx}/{total_files} berkas...")
        except Exception as e:
            logger.error(f"Gagal meng-audit berkas {filepath}: {e}")

    # Hitung rata-rata confidence
    avg_confidence = total_confidence / total_files if total_files > 0 else 0.0

    # Ringkasan statistik di konsol
    logger.info("======================================================================")
    logger.info("                      RINGKASAN HASIL AUDIT")
    logger.info("======================================================================")
    logger.info(f"Total File Diaudit       : {total_files}")
    logger.info(f"Rata-rata Confidence Score: {avg_confidence:.1f}%")
    logger.info(f"  - AUTO_SORT            : {stats['AUTO_SORT']} file ({stats['AUTO_SORT']/total_files*100:.1f}%)")
    logger.info(f"  - SUGGESTED REVIEW     : {stats['REVIEW_WITH_SUGGESTION']} file ({stats['REVIEW_WITH_SUGGESTION']/total_files*100:.1f}%)")
    logger.info(f"  - NEEDS REVIEW         : {stats['NEEDS_REVIEW']} file ({stats['NEEDS_REVIEW']/total_files*100:.1f}%)")
    logger.info(f"  - REJECT (BAD AUDIO)   : {stats['REJECT_BAD_AUDIO']} file ({stats['REJECT_BAD_AUDIO']/total_files*100:.1f}%)")
    logger.info("======================================================================")

    # Tulis laporan audit
    csv_path = os.path.join(logs_dir, "classification_report.csv")
    xlsx_path = os.path.join(logs_dir, "classification_report.xlsx")
    
    write_csv_report(classification_records, csv_path, CLASSIFY_COLUMNS)
    convert_csv_to_xlsx(csv_path, xlsx_path)

    logger.info(f"Laporan audit berhasil disimpan ke: {csv_path} | {xlsx_path}")
    return classification_records


if __name__ == "__main__":
    setup_logger()
    
    parser = argparse.ArgumentParser(description="Audit Klasifikasi Audio Standalone v3.0")
    parser.add_argument("--input", default="data/input", help="Folder input berkas audio")
    parser.add_argument("--output-dir", default="data/logs", help="Folder logs hasil audit")
    
    args = parser.parse_args()
    run_classification_audit(input_dir=args.input, logs_dir=args.output_dir)
