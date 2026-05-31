"""
scripts/05_sort_to_radio_folders.py — Sortir Audio ke Folder Master Radio v3.0
================================================================================
Memindahkan file audio ke struktur folder RADIO_AUDIO_MASTER_LIBRARY/ berdasarkan
hasil klasifikasi confidence-based dari audio_classifier.py v3.0.

Prinsip:
  - AUTO_SORT     → masuk folder master final (target_folder)
  - REVIEW_*      → masuk review_folder spesifik di 90_NEEDS_REVIEW/
  - NEEDS_REVIEW  → masuk review_folder spesifik di 90_NEEDS_REVIEW/
  - REJECT_BAD    → masuk 92_BAD_AUDIO/
  - File asli TIDAK dihapus. Tidak ada overwrite. Tidak ada delete otomatis.
"""

import os
import csv
import logging
from typing import List, Dict, Any

from src.utils import load_json_config, setup_logger
from src.audio_classifier import classify_audio_file
from src.safe_file_ops import safe_copy_file
from src.batch_manager import BatchManager
from src.report_writer import write_csv_report, convert_csv_to_xlsx

logger = logging.getLogger("RADIO_MUSIC_CLEANER")

# Kolom laporan sortir v3.0
SORT_COLUMNS = [
    "source_path", "current_batch_path", "filename",
    "media_type", "master_bucket", "target_folder", "review_folder",
    "confidence_score", "decision", "final_destination_type",
    "actual_dest_path", "signals", "warnings", "conflicts",
    "classification_reason", "sort_status", "sort_notes"
]

# Kolom laporan klasifikasi (untuk classification_report.csv)
CLASSIFY_COLUMNS = [
    "source_path", "filename", "media_type", "master_bucket",
    "target_folder", "review_folder", "confidence_score",
    "decision", "signals", "warnings", "conflicts", "reason"
]


def sort_to_radio_folders(
    batch_id: str,
    final_output_dir: str = "data/output/RADIO_AUDIO_MASTER_LIBRARY",
    logs_dir: str = "data/logs",
    resume: bool = False,
    dry_run: bool = False,
) -> List[Dict[str, Any]]:
    """
    Menyusun file audio ke struktur folder master radio berdasarkan decision classifier.

    Parameter:
        batch_id        : ID batch yang akan disortir
        final_output_dir: Root folder output (default: RADIO_AUDIO_MASTER_LIBRARY)
        logs_dir        : Direktori laporan
        resume          : Lanjut dari sesi sebelumnya
        dry_run         : Preview tanpa menyalin file fisik
    """
    logger.info("=== Memulai Sortir Audio ke Folder Master Radio v3.0 ===")

    os.makedirs(final_output_dir, exist_ok=True)

    # Inisialisasi Batch Manager
    batch_mgr = BatchManager(logs_dir)
    batch_records = batch_mgr.get_all_records_for_batch(batch_id)

    if not batch_records:
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
                                "sort_status": "PENDING"
                            })
            except Exception as e:
                logger.error(f"Gagal membaca filename_cleaning_applied.csv: {e}")

    # Saring file yang siap disortir
    target_records = [
        r for r in batch_records
        if r.get("rename_status") == "SUCCESS" and r.get("target_path")
    ]

    if not target_records:
        logger.error("Tidak ada file audio yang siap disortir.")
        return []

    logger.info(f"Ditemukan {len(target_records)} file audio yang siap disortir.")

    # Muat data scan untuk metadata tambahan
    scan_report_path = os.path.join(logs_dir, "audio_scan_report.csv")
    scan_data_map: Dict[str, Dict[str, Any]] = {}

    if os.path.exists(scan_report_path):
        try:
            with open(scan_report_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    key = row.get("original_path", "") or row.get("source_path", "")
                    if key:
                        scan_data_map[key] = row
        except Exception as e:
            logger.error(f"Gagal memuat peta data scan: {e}")

    # Proses sortir
    sorting_records: List[Dict[str, Any]] = []
    classification_records: List[Dict[str, Any]] = []

    counts = {
        "AUTO_SORT": 0, "REVIEW_WITH_SUGGESTION": 0,
        "NEEDS_REVIEW": 0, "REJECT_BAD_AUDIO": 0,
        "FAILED": 0, "SKIPPED": 0
    }

    for idx, row in enumerate(target_records, 1):
        src_path         = row.get("source_path", "")
        current_batch_path = row.get("target_path", "")

        if not current_batch_path or not os.path.exists(current_batch_path):
            logger.warning(f"File tidak ditemukan: {current_batch_path}")
            continue

        # Resume check
        if resume and row.get("sort_status") == "SUCCESS":
            counts["SKIPPED"] += 1
            continue

        filename = os.path.basename(current_batch_path)

        # Ambil parent folder dari path sumber
        parent_folder = ""
        if src_path and os.path.dirname(src_path):
            parent_folder = os.path.basename(os.path.dirname(src_path))

        # Ambil info scan untuk metadata
        scan_info = scan_data_map.get(src_path, scan_data_map.get(current_batch_path, {}))

        duration_raw = scan_info.get("duration_seconds", 0)
        try:
            duration = float(duration_raw) if duration_raw else None
        except (ValueError, TypeError):
            duration = None

        # ── KLASIFIKASI ULANG dengan classify_audio_file() v3.0 ─────────────
        clf = classify_audio_file(
            filename        = filename,
            source_path     = current_batch_path,
            parent_folder   = parent_folder,
            duration_seconds= duration,
            genre_tag       = scan_info.get("genre_tag", ""),
            artist_tag      = scan_info.get("artist_tag", ""),
            title_tag       = scan_info.get("title_tag", ""),
            album_tag       = scan_info.get("album_tag", ""),
            year_tag        = scan_info.get("year_tag", ""),
        )

        decision          = clf["decision"]
        media_type        = clf["media_type"]
        master_bucket     = clf["master_bucket"]
        target_folder     = clf["target_folder"]
        review_folder     = clf["review_folder"]
        confidence_score  = clf["confidence_score"]
        signals           = "; ".join(clf.get("signals", []))
        warnings          = "; ".join(clf.get("warnings", []))
        conflicts         = "; ".join(clf.get("conflicts", []))
        reason            = clf["reason"]

        # Simpan ke laporan klasifikasi
        classification_records.append({
            "source_path":     src_path,
            "filename":        filename,
            "media_type":      media_type,
            "master_bucket":   master_bucket,
            "target_folder":   target_folder,
            "review_folder":   review_folder,
            "confidence_score": confidence_score,
            "decision":        decision,
            "signals":         signals,
            "warnings":        warnings,
            "conflicts":       conflicts,
            "reason":          reason,
        })

        # ── ROUTING BERDASARKAN DECISION v3.0 ──────────────────────────────
        if decision == "AUTO_SORT":
            dest_folder_rel      = target_folder
            final_destination_type = "MASTER_FINAL"
        elif decision == "REJECT_BAD_AUDIO":
            dest_folder_rel      = target_folder  # "92_BAD_AUDIO"
            final_destination_type = "BAD_AUDIO"
        else:
            # REVIEW_WITH_SUGGESTION atau NEEDS_REVIEW
            dest_folder_rel      = review_folder
            final_destination_type = "REVIEW"

        dest_dir = os.path.join(final_output_dir, dest_folder_rel)

        if dry_run:
            sort_status = "DRY_RUN"
            actual_dest_path = os.path.join(dest_dir, filename)
            sort_notes = f"[DRY_RUN] Akan di-copy ke: {dest_folder_rel}"
            logger.debug(f"[DRY_RUN][{decision}] {filename} → {dest_folder_rel}")
        else:
            os.makedirs(dest_dir, exist_ok=True)
            actual_dest_path, copy_res = safe_copy_file(current_batch_path, dest_dir, filename)

            if copy_res == "SUCCESS":
                sort_status = "SUCCESS"
                sort_notes  = f"{decision} | Score={confidence_score} | {reason[:100]}"
                batch_mgr.update_file_status(src_path, stage="sort", status="SUCCESS", target_path=actual_dest_path)
                counts[decision] = counts.get(decision, 0) + 1
                logger.debug(f"[{decision}] {filename} → {dest_folder_rel}")
            else:
                sort_status = "FAILED"
                sort_notes  = copy_res
                actual_dest_path = ""
                batch_mgr.update_file_status(src_path, stage="sort", status="FAILED", error_msg=copy_res)
                counts["FAILED"] += 1
                logger.error(f"Gagal menyortir {filename}: {copy_res}")

        sorting_records.append({
            "source_path":           src_path,
            "current_batch_path":    current_batch_path,
            "filename":              filename,
            "media_type":            media_type,
            "master_bucket":         master_bucket,
            "target_folder":         target_folder,
            "review_folder":         review_folder,
            "confidence_score":      confidence_score,
            "decision":              decision,
            "final_destination_type": final_destination_type,
            "actual_dest_path":      actual_dest_path,
            "signals":               signals,
            "warnings":              warnings,
            "conflicts":             conflicts,
            "classification_reason": reason,
            "sort_status":           sort_status,
            "sort_notes":            sort_notes,
        })

        if idx % 50 == 0 or idx == len(target_records):
            logger.info(f"[SORT] Memproses {idx}/{len(target_records)} berkas...")

    # ── LAPORAN RINGKASAN ──────────────────────────────────────────────────
    logger.info(
        f"[SORT] Hasil:"
        f" AUTO_SORT={counts['AUTO_SORT']}"
        f" | REVIEW_WITH_SUGGESTION={counts['REVIEW_WITH_SUGGESTION']}"
        f" | NEEDS_REVIEW={counts['NEEDS_REVIEW']}"
        f" | REJECT_BAD_AUDIO={counts['REJECT_BAD_AUDIO']}"
        f" | FAILED={counts['FAILED']}"
        f" | SKIPPED={counts['SKIPPED']}"
    )

    # Tulis laporan sortir
    csv_sort_path  = os.path.join(logs_dir, "folder_sorting_report.csv")
    xlsx_sort_path = os.path.join(logs_dir, "folder_sorting_report.xlsx")
    write_csv_report(sorting_records, csv_sort_path, SORT_COLUMNS)
    convert_csv_to_xlsx(csv_sort_path, xlsx_sort_path)

    # Tulis laporan klasifikasi terpisah
    csv_clf_path  = os.path.join(logs_dir, "classification_report.csv")
    xlsx_clf_path = os.path.join(logs_dir, "classification_report.xlsx")
    write_csv_report(classification_records, csv_clf_path, CLASSIFY_COLUMNS)
    convert_csv_to_xlsx(csv_clf_path, xlsx_clf_path)

    logger.info(f"=== Sortir folder selesai. Laporan: {csv_sort_path} | {csv_clf_path} ===")
    return sorting_records


if __name__ == "__main__":
    setup_logger()
    sort_to_radio_folders(batch_id="TEST_BATCH")
