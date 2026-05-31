"""
scripts/08_fingerprint_candidates.py — Pendeteksi Sidik Jari Audio Massal v4.0
=============================================================================
Skrip CLI stasiun radio untuk memproses sidik jari audio (fingerprinting AcoustID)
pada berkas audio musik yang ambigu atau kekurangan tag metadata.

Membaca data scan_report, menyaring lagu layak, mengekstraksi sidik jari,
dan mencatat hasil lookup AcoustID ke laporan fingerprint_report.csv/xlsx.
"""

import os
import sys
import csv
import logging
from typing import List, Dict, Any

# Pastikan root workspace masuk sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils import setup_logger, load_json_config
from src.fingerprint_lookup import (
    find_fpcalc_executable,
    calculate_audio_fingerprint,
    lookup_acoustid,
    is_eligible_for_fingerprint
)
from src.report_writer import write_csv_report, convert_csv_to_xlsx

logger = logging.getLogger("RADIO_MUSIC_CLEANER")

# Kolom laporan hasil fingerprinting stasiun radio v4.0
FINGERPRINT_COLUMNS = [
    "file_id", "file_path", "filename", "fingerprint_status", 
    "acoustid", "acoustid_score", "musicbrainz_recording_id", 
    "suggested_artist", "suggested_title", "suggested_album", 
    "suggested_year", "match_status", "skip_reason"
]


def fingerprint_candidates(
    batch_id: str = "TEST_BATCH",
    logs_dir: str = "data/logs"
) -> List[Dict[str, Any]]:
    """
    Menjalankan proses fingerprinting massal untuk seluruh kandidat file lagu yang layak.
    """
    logger.info("======================================================================")
    logger.info("      MEMULAI PROSES ACOUSTID FINGERPRINTING MASSAL v4.0")
    logger.info("======================================================================")

    # 1. Cek keberadaan fpcalc
    fpcalc_path = find_fpcalc_executable()
    if not fpcalc_path:
        logger.warning(
            "[FINGERPRINT] Executable fpcalc.exe tidak ditemukan di folder proyek atau PATH.\n"
            "   -> Silakan tempatkan file fpcalc.exe di folder 'bin/' proyek untuk mengaktifkan sidik jari audio.\n"
            "   -> Melewati proses fingerprinting AcoustID secara aman..."
        )
        # Tulis laporan kosong/lewati agar pipeline tetap berjalan mulus
        csv_path = os.path.join(logs_dir, "fingerprint_report.csv")
        xlsx_path = os.path.join(logs_dir, "fingerprint_report.xlsx")
        write_csv_report([], csv_path, FINGERPRINT_COLUMNS)
        convert_csv_to_xlsx(csv_path, xlsx_path)
        return []

    # 2. Muat laporan scan audio_scan_report
    scan_report_path = os.path.join(logs_dir, "audio_scan_report.csv")
    if not os.path.exists(scan_report_path):
        logger.error(f"[FINGERPRINT] audio_scan_report.csv tidak ditemukan di {scan_report_path}. Silakan jalankan scan dahulu.")
        return []

    scan_records: List[Dict[str, Any]] = []
    try:
        with open(scan_report_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            scan_records = list(reader)
    except Exception as e:
        logger.error(f"[FINGERPRINT] Gagal membaca laporan scan: {e}")
        return []

    total_files = len(scan_records)
    logger.info(f"Membaca {total_files} file hasil scan library.")

    fingerprint_records: List[Dict[str, Any]] = []
    eligible_count = 0
    match_count = 0

    # 3. Iterasi dan proses sidik jari audio
    for idx, row in enumerate(scan_records, 1):
        file_id = row.get("id", f"FID-{idx:05d}")
        filepath = row.get("original_path", "")
        filename = row.get("filename", "")
        media_type = row.get("media_type", "MUSIC")
        
        try:
            duration = float(row.get("duration_seconds", 0))
        except ValueError:
            duration = 0.0

        try:
            conf_score = float(row.get("confidence_score", 100))
        except ValueError:
            conf_score = 100.0

        decision = row.get("decision", "NEEDS_REVIEW")

        # Cek kelayakan berkas audio untuk fingerprinting
        is_eligible, skip_reason = is_eligible_for_fingerprint(
            media_type=media_type,
            duration_seconds=duration,
            confidence_score=conf_score,
            decision=decision,
            filename=filename
        )

        if not is_eligible:
            # Lewati berkas secara aman dengan mencatat alasannya
            fingerprint_records.append({
                "file_id": file_id,
                "file_path": filepath,
                "filename": filename,
                "fingerprint_status": "SKIPPED",
                "acoustid": "",
                "acoustid_score": "",
                "musicbrainz_recording_id": "",
                "suggested_artist": "",
                "suggested_title": "",
                "suggested_album": "",
                "suggested_year": "",
                "match_status": "SKIP",
                "skip_reason": skip_reason
            })
            continue

        eligible_count += 1
        logger.info(f"[FINGERPRINT] Memproses berkas layak ({eligible_count}): {filename}")

        # Jalankan ekstraksi sidik jari
        fp_res = calculate_audio_fingerprint(filepath, fpcalc_path)
        if not fp_res:
            fingerprint_records.append({
                "file_id": file_id,
                "file_path": filepath,
                "filename": filename,
                "fingerprint_status": "FAILED_FPCALC",
                "acoustid": "",
                "acoustid_score": "",
                "musicbrainz_recording_id": "",
                "suggested_artist": "",
                "suggested_title": "",
                "suggested_album": "",
                "suggested_year": "",
                "match_status": "ERROR",
                "skip_reason": "fpcalc gagal mengekstrak sidik jari audio"
            })
            continue

        actual_duration, fp_string = fp_res

        # Lookup database AcoustID Web Service
        match_data = lookup_acoustid(actual_duration, fp_string)
        if not match_data:
            fingerprint_records.append({
                "file_id": file_id,
                "file_path": filepath,
                "filename": filename,
                "fingerprint_status": "SUCCESS_FPCALC",
                "acoustid": "",
                "acoustid_score": "",
                "musicbrainz_recording_id": "",
                "suggested_artist": "",
                "suggested_title": "",
                "suggested_album": "",
                "suggested_year": "",
                "match_status": "NO_MATCH",
                "skip_reason": "Tidak ada sidik jari lagu yang cocok di database AcoustID"
            })
            continue

        # Ditemukan kecocokan lagu resmi
        match_count += 1
        fingerprint_records.append({
            "file_id": file_id,
            "file_path": filepath,
            "filename": filename,
            "fingerprint_status": "SUCCESS_ACOUSTID",
            "acoustid": match_data["acoustid"],
            "acoustid_score": match_data["acoustid_score"],
            "musicbrainz_recording_id": match_data["musicbrainz_recording_id"],
            "suggested_artist": match_data["suggested_artist"],
            "suggested_title": match_data["suggested_title"],
            "suggested_album": match_data["suggested_album"],
            "suggested_year": match_data["suggested_year"],
            "match_status": "MATCHED",
            "skip_reason": "AcoustID sidik jari teridentifikasi"
        })

    # 4. Tulis laporan akhir
    csv_path = os.path.join(logs_dir, "fingerprint_report.csv")
    xlsx_path = os.path.join(logs_dir, "fingerprint_report.xlsx")
    
    write_csv_report(fingerprint_records, csv_path, FINGERPRINT_COLUMNS)
    convert_csv_to_xlsx(csv_path, xlsx_path)

    logger.info("======================================================================")
    logger.info("                      RINGKASAN SIKLUS FINGERPRINT")
    logger.info("======================================================================")
    logger.info(f"Total Berkas Scan  : {total_files}")
    logger.info(f"Kandidat Layak     : {eligible_count}")
    logger.info(f"Lagu Teridentifikasi: {match_count}")
    logger.info(f"Laporan disimpan ke: {csv_path}")
    logger.info("======================================================================")

    return fingerprint_records


if __name__ == "__main__":
    setup_logger()
    fingerprint_candidates()
