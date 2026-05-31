"""
src/metadata_suggestion_engine.py — Mesin Evaluator Usulan Metadata v4.0
========================================================================
Mengevaluasi usulan metadata hasil AcoustID sidik jari dan melakukan kueri
lanjutan ke MusicBrainz Web Service untuk mendapatkan data album, tahun, dan genre resmi.

Membandingkan usulan dengan tag asli pada disk dan mengelompokkan status menjadi:
AUTO_WRITE_EMPTY_TAGS, SUGGEST_ONLY, REVIEW_CONFLICT, LOW_CONFIDENCE, dll.
"""

import os
import csv
import logging
from typing import List, Dict, Any, Tuple

from src.utils import load_json_config
from src.musicbrainz_client import query_musicbrainz_recording
from src.report_writer import write_csv_report, convert_csv_to_xlsx

logger = logging.getLogger("RADIO_MUSIC_CLEANER")

# Kolom laporan usulan metadata stasiun radio v4.0
SUGGESTION_COLUMNS = [
    "file_id", "file_path", "filename", "media_type", 
    "current_artist", "current_title", "current_album", "current_genre", "current_year", 
    "suggested_artist", "suggested_title", "suggested_album", "suggested_genre", "suggested_year", 
    "musicbrainz_recording_id", "acoustid_score", "metadata_write_mode", "conflict_detected", "notes"
]


def evaluate_metadata_suggestions(
    logs_dir: str = "data/logs"
) -> List[Dict[str, Any]]:
    """
    Mengevaluasi usulan metadata sidik jari audio dengan membandingkan tag asli
    dan menyelaraskan data dengan kueri lanjutan MusicBrainz API.
    """
    logger.info("=== Memulai Analisis Evaluasi Usulan Metadata Cerdas v4.0 ===")

    fingerprint_report_path = os.path.join(logs_dir, "fingerprint_report.csv")
    scan_report_path = os.path.join(logs_dir, "audio_scan_report.csv")

    if not os.path.exists(fingerprint_report_path):
        logger.error(f"[SUGGESTION] Laporan sidik jari tidak ditemukan di {fingerprint_report_path}. Silakan jalankan fingerprint dahulu.")
        return []

    # 1. Muat laporan scan asli untuk mengambil metadata saat ini (current tag)
    scan_data_map: Dict[str, Dict[str, Any]] = {}
    if os.path.exists(scan_report_path):
        try:
            with open(scan_report_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    path = row.get("original_path", "")
                    if path:
                        scan_data_map[path] = row
        except Exception as e:
            logger.error(f"[SUGGESTION] Gagal membaca laporan scan: {e}")

    # 2. Muat laporan AcoustID fingerprint
    fingerprint_records: List[Dict[str, Any]] = []
    try:
        with open(fingerprint_report_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fingerprint_records = list(reader)
    except Exception as e:
        logger.error(f"[SUGGESTION] Gagal membaca laporan sidik jari: {e}")
        return []

    suggestion_records: List[Dict[str, Any]] = []
    total_analyzed = 0
    auto_write_count = 0
    conflict_count = 0

    # 3. Evaluasi masing-masing berkas
    for idx, fp_row in enumerate(fingerprint_records, 1):
        file_path = fp_row.get("file_path", "")
        filename = fp_row.get("filename", "")
        file_id = fp_row.get("file_id", f"FID-{idx:05d}")
        match_status = fp_row.get("match_status", "SKIP")
        skip_reason = fp_row.get("skip_reason", "")

        # Ambil info scan saat ini
        scan_info = scan_data_map.get(file_path, {})
        media_type = scan_info.get("media_type") or "MUSIC"
        
        current_artist = scan_info.get("artist_tag", "").strip()
        current_title = scan_info.get("title_tag", "").strip()
        current_album = scan_info.get("album_tag", "").strip()
        current_genre = scan_info.get("genre_tag", "").strip()
        current_year = scan_info.get("year_tag", "").strip()

        # A. Kasus non-kelayakan / dilewati aman
        if match_status == "SKIP":
            suggestion_records.append({
                "file_id": file_id,
                "file_path": file_path,
                "filename": filename,
                "media_type": media_type,
                "current_artist": current_artist,
                "current_title": current_title,
                "current_album": current_album,
                "current_genre": current_genre,
                "current_year": current_year,
                "suggested_artist": "",
                "suggested_title": "",
                "suggested_album": "",
                "suggested_genre": "",
                "suggested_year": "",
                "musicbrainz_recording_id": "",
                "acoustid_score": "",
                "metadata_write_mode": "SKIP_NON_MUSIC",
                "conflict_detected": "NO",
                "notes": f"Dilewati karena: {skip_reason}"
            })
            continue

        # B. Kasus fingerprint gagal/tidak cocok
        if match_status in ("NO_MATCH", "ERROR"):
            suggestion_records.append({
                "file_id": file_id,
                "file_path": file_path,
                "filename": filename,
                "media_type": media_type,
                "current_artist": current_artist,
                "current_title": current_title,
                "current_album": current_album,
                "current_genre": current_genre,
                "current_year": current_year,
                "suggested_artist": "",
                "suggested_title": "",
                "suggested_album": "",
                "suggested_genre": "",
                "suggested_year": "",
                "musicbrainz_recording_id": "",
                "acoustid_score": "",
                "metadata_write_mode": "NO_MATCH" if match_status == "NO_MATCH" else "LOW_CONFIDENCE",
                "conflict_detected": "NO",
                "notes": f"Sidik jari audio tidak menghasilkan kecocokan: {skip_reason}"
            })
            continue

        # C. Kasus lagu resmi teridentifikasi (MATCHED)
        total_analyzed += 1
        recording_id = fp_row.get("musicbrainz_recording_id", "")
        acoustid_score_str = fp_row.get("acoustid_score", "0")
        try:
            score = float(acoustid_score_str)
        except ValueError:
            score = 0.0

        # Kueri detail metadata lanjutan dari MusicBrainz API untuk data album & tahun resmi
        mb_artist = fp_row.get("suggested_artist", "")
        mb_title = fp_row.get("suggested_title", "")
        mb_album = fp_row.get("suggested_album", "")
        mb_year = fp_row.get("suggested_year", "")
        mb_genre = ""

        if recording_id:
            logger.info(f"[SUGGESTION] Lookup lanjutan MusicBrainz untuk Recording ID: {recording_id}")
            mb_data = query_musicbrainz_recording(recording_id)
            if mb_data:
                mb_artist = mb_data.get("suggested_artist") or mb_artist
                mb_title = mb_data.get("suggested_title") or mb_title
                mb_album = mb_data.get("suggested_album") or mb_album
                mb_year = mb_data.get("suggested_year") or mb_year
                mb_genre = mb_data.get("suggested_genre") or ""

        # Bersihkan spasi
        mb_artist = mb_artist.strip()
        mb_title = mb_title.strip()
        mb_album = mb_album.strip()
        mb_year = mb_year.strip()
        mb_genre = mb_genre.strip()

        # Bandingkan usulan metadata dengan tag asli
        conflict_detected = "NO"
        metadata_write_mode = "SUGGEST_ONLY"
        notes = "Usulan opsional AcoustID."

        # Cek kekosongan tag dasar
        tags_empty = not current_artist and not current_title

        if tags_empty:
            if score >= 0.90:
                metadata_write_mode = "AUTO_WRITE_EMPTY_TAGS"
                notes = "AcoustID kecocokan tinggi (score >= 0.90), tag asli kosong. Siap auto-apply."
                auto_write_count += 1
            else:
                metadata_write_mode = "SUGGEST_ONLY"
                notes = "Kecocokan AcoustID sedang, tag asli kosong. Butuh review."
        else:
            # Tag asli ada, bandingkan kesamaan nama artis & judul
            artist_different = current_artist.lower() != mb_artist.lower()
            title_different = current_title.lower() != mb_title.lower()
            
            if artist_different or title_different:
                metadata_write_mode = "REVIEW_CONFLICT"
                conflict_detected = "YES"
                notes = f"Konflik Tag! Asli='{current_artist} - {current_title}' vs Usulan='{mb_artist} - {mb_title}'"
                conflict_count += 1
            else:
                # Tag penting sama, tetapi album/tahun kosong atau berbeda ringan
                metadata_write_mode = "SUGGEST_ONLY"
                notes = "Tag lagu penting sama, menyarankan pengisian album/tahun jika kosong."

        suggestion_records.append({
            "file_id": file_id,
            "file_path": file_path,
            "filename": filename,
            "media_type": media_type,
            "current_artist": current_artist,
            "current_title": current_title,
            "current_album": current_album,
            "current_genre": current_genre,
            "current_year": current_year,
            "suggested_artist": mb_artist,
            "suggested_title": mb_title,
            "suggested_album": mb_album,
            "suggested_genre": mb_genre,
            "suggested_year": mb_year,
            "musicbrainz_recording_id": recording_id,
            "acoustid_score": round(score, 3),
            "metadata_write_mode": metadata_write_mode,
            "conflict_detected": conflict_detected,
            "notes": notes
        })

    # Tulis laporan
    csv_path = os.path.join(logs_dir, "metadata_suggestions.csv")
    xlsx_path = os.path.join(logs_dir, "metadata_suggestions.xlsx")
    
    write_csv_report(suggestion_records, csv_path, SUGGESTION_COLUMNS)
    convert_csv_to_xlsx(csv_path, xlsx_path)

    logger.info("======================================================================")
    logger.info("                      RINGKASAN METADATA SUGGESTIONS")
    logger.info("======================================================================")
    logger.info(f"Total Lagu Dievaluasi   : {total_analyzed}")
    logger.info(f"Auto-Write Aman (Empty) : {auto_write_count}")
    logger.info(f"Konflik Tag Terdeteksi  : {conflict_count}")
    logger.info(f"Laporan usulan disimpan: {csv_path}")
    logger.info("======================================================================")

    return suggestion_records


if __name__ == "__main__":
    from src.utils import setup_logger
    setup_logger()
    evaluate_metadata_suggestions()
