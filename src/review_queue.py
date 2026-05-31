"""
src/review_queue.py — Pusat Validasi Antrean Tinjauan Operator v4.0
==================================================================
Merangkum hasil klasifikasi fisik, audit nama file, deteksi duplikat,
dan usulan metadata AcoustID/MusicBrainz ke dalam satu struktur
draf antrean tinjauan (review queue) terpadu bagi operator stasiun radio.

Mengalokasikan subfolder tinjauan fisik di bawah 90_NEEDS_REVIEW/
berdasarkan jenis konflik spesifik agar memudahkan peninjauan manual.
"""

import os
import csv
import logging
from typing import List, Dict, Any

from src.utils import load_json_config
from src.report_writer import write_csv_report, convert_csv_to_xlsx

logger = logging.getLogger("RADIO_MUSIC_CLEANER")

# Kolom antrean tinjauan operator stasiun radio v4.0
REVIEW_COLUMNS = [
    "file_id", "file_path", "filename", "media_type", 
    "current_artist", "current_title", "suggested_artist", "suggested_title", 
    "suggested_album", "suggested_year", "target_folder_suggestion", 
    "confidence_score", "review_reason", "status", "operator_decision", "operator_notes"
]


def build_review_queue_draft(
    logs_dir: str = "data/logs"
) -> List[Dict[str, Any]]:
    """
    Membangun draf antrean tinjauan operator (review queue) dengan mengintegrasikan
    laporan sortir klasifikasi fisik dan laporan usulan metadata AcoustID/MusicBrainz.
    """
    logger.info("=== Memulai Pembangunan Draf Antrean Tinjauan Operator v4.0 ===")

    sort_report_path = os.path.join(logs_dir, "folder_sorting_report.csv")
    suggestions_path = os.path.join(logs_dir, "metadata_suggestions.csv")

    if not os.path.exists(sort_report_path):
        logger.error(f"[REVIEW] Laporan sortir tidak ditemukan di {sort_report_path}. Silakan jalankan sortir/scan dahulu.")
        return []

    # 1. Muat laporan sortir fisik (folder_sorting_report)
    sort_records: List[Dict[str, Any]] = []
    try:
        with open(sort_report_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            sort_records = list(reader)
    except Exception as e:
        logger.error(f"[REVIEW] Gagal membaca laporan sortir: {e}")
        return []

    # 2. Muat laporan usulan metadata (metadata_suggestions)
    suggestions_map: Dict[str, Dict[str, Any]] = {}
    if os.path.exists(suggestions_path):
        try:
            with open(suggestions_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    path = row.get("file_path", "")
                    if path:
                        suggestions_map[path] = row
        except Exception as e:
            logger.error(f"[REVIEW] Gagal membaca laporan usulan metadata: {e}")

    review_records: List[Dict[str, Any]] = []
    pending_count = 0
    approved_count = 0

    # 3. Iterasi penggabungan data secara atomik
    for idx, sort_row in enumerate(sort_records, 1):
        file_path = sort_row.get("current_batch_path", "") or sort_row.get("source_path", "")
        filename = sort_row.get("filename", "")
        
        # Cari data usulan metadata AcoustID/MusicBrainz
        sug_info = suggestions_map.get(file_path, suggestions_map.get(sort_row.get("source_path", ""), {}))

        media_type = sort_row.get("media_type") or sug_info.get("media_type") or "MUSIC"
        decision = sort_row.get("decision") or "NEEDS_REVIEW"
        
        confidence_raw = sort_row.get("confidence_score") or sug_info.get("acoustid_score") or "100"
        try:
            confidence = float(confidence_raw)
        except ValueError:
            confidence = 100.0

        current_artist = sug_info.get("current_artist") or sort_row.get("artist_tag", "")
        current_title = sug_info.get("current_title") or sort_row.get("title_tag", "")
        
        suggested_artist = sug_info.get("suggested_artist", "")
        suggested_title = sug_info.get("suggested_title", "")
        suggested_album = sug_info.get("suggested_album", "")
        suggested_year = sug_info.get("suggested_year", "")
        
        metadata_mode = sug_info.get("metadata_write_mode", "SKIP_NON_MUSIC")
        conflict_detected = sug_info.get("conflict_detected", "NO")
        clf_reason = sort_row.get("classification_reason", "")
        sug_notes = sug_info.get("notes", "")

        # A. Susun alasan peninjauan komprehensif (review reason)
        reasons_list = []
        if clf_reason:
            reasons_list.append(clf_reason)
        if conflict_detected == "YES":
            reasons_list.append("Konflik Tag Metadata")
        if metadata_mode == "LOW_CONFIDENCE":
            reasons_list.append("Confidence AcoustID rendah")
        if metadata_mode == "NO_MATCH" and media_type == "MUSIC":
            reasons_list.append("Sidik jari audio tidak cocok di database AcoustID")

        review_reason = " | ".join(reasons_list) if reasons_list else "Klasifikasi aman, tidak butuh review"

        # B. Tentukan status review draft default stasiun radio
        # APPROVED: Lulus otomatis (confidence tinggi dan tanpa konflik metadata)
        # PENDING_REVIEW: Harus ditinjau (skor rendah, ada konflik tag, dll)
        if decision == "AUTO_SORT" and conflict_detected == "NO" and metadata_mode in ("AUTO_WRITE_EMPTY_TAGS", "SKIP_NON_MUSIC", "SUGGEST_ONLY"):
            status = "APPROVED"
            operator_decision = "AUTO_SORTED"
            operator_notes = "Disetujui otomatis oleh sistem (skor tinggi)."
            target_folder_suggestion = sort_row.get("target_folder", "")
            approved_count += 1
        elif decision == "REJECT_BAD_AUDIO":
            status = "REJECTED"
            operator_decision = "REJECT"
            operator_notes = "Ditolak otomatis oleh sistem (berkas audio corrupt)."
            target_folder_suggestion = "92_BAD_AUDIO"
            approved_count += 1
        else:
            status = "PENDING_REVIEW"
            operator_decision = ""
            operator_notes = ""
            pending_count += 1
            
            # C. Logika Alokasi Subfolder Tinjauan Fisik stasiun radio v4.0
            # Operator dapat memverifikasi file di folder khusus ini
            review_sub = "90_NEEDS_REVIEW/02_LOW_CONFIDENCE_CATEGORY"
            
            if "WhatsApp" in review_reason or "ambigu" in review_reason.lower() or "AMBIGUOUS" in review_reason:
                review_sub = "90_NEEDS_REVIEW/01_UNKNOWN_ARTIST_TITLE"
            elif conflict_detected == "YES":
                review_sub = "90_NEEDS_REVIEW/14_MUSICBRAINZ_METADATA_CONFLICT"
            elif metadata_mode == "NO_MATCH" and media_type == "MUSIC":
                review_sub = "90_NEEDS_REVIEW/11_FINGERPRINT_NO_MATCH"
            elif metadata_mode == "LOW_CONFIDENCE" and media_type == "MUSIC":
                review_sub = "90_NEEDS_REVIEW/13_FINGERPRINT_LOW_CONFIDENCE"
            elif "konflik" in review_reason.lower() or "CONFLICT" in review_reason:
                review_sub = "90_NEEDS_REVIEW/03_CONFLICTING_SIGNALS"
                
            target_folder_suggestion = review_sub

        file_id = sort_row.get("file_id") or sug_info.get("file_id") or f"FID-{idx:05d}"

        review_records.append({
            "file_id": file_id,
            "file_path": file_path,
            "filename": filename,
            "media_type": media_type,
            "current_artist": current_artist,
            "current_title": current_title,
            "suggested_artist": suggested_artist,
            "suggested_title": suggested_title,
            "suggested_album": suggested_album,
            "suggested_year": suggested_year,
            "target_folder_suggestion": target_folder_suggestion,
            "confidence_score": round(confidence, 1),
            "review_reason": review_reason,
            "status": status,
            "operator_decision": operator_decision,
            "operator_notes": operator_notes
        })

    # Tulis laporan
    csv_path = os.path.join(logs_dir, "review_queue.csv")
    xlsx_path = os.path.join(logs_dir, "review_queue.xlsx")
    
    write_csv_report(review_records, csv_path, REVIEW_COLUMNS)
    convert_csv_to_xlsx(csv_path, xlsx_path)

    logger.info("======================================================================")
    logger.info("                      RINGKASAN REVIEW QUEUE DRAFT")
    logger.info("======================================================================")
    logger.info(f"Total Berkas Diproses   : {len(review_records)}")
    logger.info(f"Draf Approved (Aman)    : {approved_count}")
    logger.info(f"Draf Pending (Tinjauan) : {pending_count}")
    logger.info(f"Laporan antrean disimpan: {csv_path}")
    logger.info("======================================================================")

    return review_records


if __name__ == "__main__":
    from src.utils import setup_logger
    setup_logger()
    build_review_queue_draft()
