import os
import csv
import logging
import shutil
from typing import List, Dict, Any

from src.utils import load_json_config, setup_logger
from src.audio_classifier import classify_audio
from src.safe_file_ops import safe_copy_file, make_windows_safe_path
from src.batch_manager import BatchManager
from src.report_writer import write_csv_report, convert_csv_to_xlsx

# Kolom untuk laporan sortir folder
SORT_COLUMNS = [
    "source_path", "target_path", "old_filename", "new_filename",
    "sorted_folder", "confidence_score", "decision", "status", "notes"
]

def sort_to_radio_folders(
    batch_id: str,
    final_output_dir: str = "data/output/RADIO_AUDIO_LIBRARY",
    logs_dir: str = "data/logs",
    resume: bool = False
) -> List[Dict[str, Any]]:
    """
    Menyusun file audio hasil salinan yang bersih ke dalam struktur folder radio kategori.
    Membaca data manifest untuk menemukan file yang sukses ditulis metadata / rename.
    """
    logger = logging.getLogger("RADIO_MUSIC_CLEANER")
    logger.info("=== Memulai Sortir Audio ke Folder Radio ===")
    
    # 1. Pastikan folder output final ada
    os.makedirs(final_output_dir, exist_ok=True)
    
    # 2. Muat konfigurasi
    classifier_config = load_json_config("config/classifier_config.json", {})
    review_subfolders = classifier_config.get("review_subfolders", {
        "low_confidence": "90_NEEDS_REVIEW/LOW_CONFIDENCE_MUSIC",
        "insufficient_data": "90_NEEDS_REVIEW/INSUFFICIENT_DATA",
        "genre_conflict": "90_NEEDS_REVIEW/GENRE_CONFLICT",
        "ambiguous_filename": "90_NEEDS_REVIEW/AMBIGUOUS_FILENAME",
        "possible_non_music": "90_NEEDS_REVIEW/POSSIBLE_NON_MUSIC"
    })
    
    # 3. Inisialisasi Batch Manager
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
                                "metadata_status": "SUCCESS",
                                "sort_status": "PENDING"
                            })
            except Exception as e:
                logger.error(f"Gagal membaca filename_cleaning_applied.csv: {e}")

    # Saring file yang siap disortir (rename_status SUCCESS dan target_path terisi)
    target_records = [r for r in batch_records if r.get("rename_status") == "SUCCESS" and r.get("target_path")]
    
    if not target_records:
        logger.error("Tidak ada file audio yang siap disortir.")
        return []
        
    logger.info(f"Ditemukan {len(target_records)} file audio hasil pembersihan yang siap disortir.")
    
    sorting_records: List[Dict[str, Any]] = []
    processed_count = 0
    
    # Muat data scan untuk mendapatkan usulan folder target
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

    # 4. Proses sortir
    counts = {"AUTO_SORT": 0, "REVIEW_WITH_SUGGESTION": 0, "NEEDS_REVIEW": 0, "FAILED": 0, "SKIPPED": 0}
    
    for row in target_records:
        src_path = row.get("source_path")  # Path file asli
        current_batch_path = row.get("target_path")  # Path file bersih sementara di output_batch
        
        # Validasi path fisik file sementara
        if not current_batch_path or not os.path.exists(current_batch_path):
            logger.warning(f"File sementara di output_batch tidak ditemukan: {current_batch_path}")
            continue
            
        # Cek resume
        if resume and row.get("sort_status") == "SUCCESS":
            logger.info(f"Resume: Skip sortir untuk {os.path.basename(current_batch_path)}")
            sorting_records.append({
                "source_path": current_batch_path,
                "target_path": row.get("target_path"),
                "old_filename": os.path.basename(current_batch_path),
                "new_filename": os.path.basename(current_batch_path),
                "sorted_folder": "",
                "confidence_score": "",
                "decision": "SKIPPED",
                "status": "SKIPPED",
                "notes": "Dilewati karena sudah selesai pada sesi sebelumnya (Resume)"
            })
            counts["SKIPPED"] += 1
            continue

        # ── KLASIFIKASI ULANG UNTUK SORTIR ──────────────────────────────────
        # Baca data scan yang sudah tersimpan (lebih efisien dari scan ulang)
        scan_info = scan_data_map.get(src_path, {})
        filename = os.path.basename(current_batch_path)
        
        # Dapatkan parent folder dari path sumber asli
        if src_path:
            input_dir_path = os.path.dirname(src_path)
            rel = os.path.relpath(src_path, start=os.path.commonpath([src_path, input_dir_path]))
            parent_folder = os.path.dirname(rel)
            if parent_folder == ".":
                parent_folder = ""
        else:
            parent_folder = scan_info.get("parent_folder", "")

        # Coba ambil decision dari scan_info terlebih dahulu (sudah diklasifikasi)
        cached_decision = scan_info.get("decision", "")
        cached_folder = scan_info.get("suggested_folder", "")
        cached_score = scan_info.get("confidence_score", "")
        
        if cached_decision and cached_folder:
            # Gunakan hasil klasifikasi dari scan
            decision = cached_decision
            suggested_folder = cached_folder
            confidence_score = cached_score
            notes_reason = scan_info.get("classifier_reason", "Dari cache scan")
        else:
            # Klasifikasi ulang jika data scan tidak tersedia
            clf_result = classify_audio(
                filename=filename,
                artist_tag=scan_info.get("artist_tag", ""),
                title_tag=scan_info.get("title_tag", ""),
                genre_tag=scan_info.get("genre_tag", ""),
                duration_seconds=float(scan_info.get("duration_seconds", 0) or 0),
                parent_folder=parent_folder,
                config=classifier_config
            )
            decision = clf_result["decision"]
            suggested_folder = clf_result["target_folder"]
            confidence_score = clf_result["confidence_score"]
            notes_reason = clf_result["reason"]

        # ── ROUTING BERDASARKAN DECISION ─────────────────────────────────────
        if decision == "AUTO_SORT":
            dest_folder_rel = suggested_folder
        elif decision == "REVIEW_WITH_SUGGESTION":
            # Masuk LOW_CONFIDENCE_MUSIC, saran disimpan di notes
            dest_folder_rel = review_subfolders.get("low_confidence", "90_NEEDS_REVIEW/LOW_CONFIDENCE_MUSIC")
            # Ambil saran folder dari signal SUGGESTION_ONLY jika ada
            suggestion_note = ""
            if scan_info.get("signals_summary"):
                suggestion_note = f" [Saran: {cached_folder}]"
            notes_reason = f"Confidence sedang ({confidence_score}/100){suggestion_note} — masuk LOW_CONFIDENCE untuk review manual"
        else:  # NEEDS_REVIEW
            # Routing ke subfolder yang tepat berdasarkan peringatan
            warnings_str = scan_info.get("warnings_summary", "")
            if "Genre" in warnings_str or "konflik" in warnings_str.lower():
                dest_folder_rel = review_subfolders.get("genre_conflict", "90_NEEDS_REVIEW/GENRE_CONFLICT")
            elif "ambigu" in notes_reason.lower() or "ambigu" in warnings_str.lower():
                dest_folder_rel = review_subfolders.get("ambiguous_filename", "90_NEEDS_REVIEW/AMBIGUOUS_FILENAME")
            elif "pendek" in notes_reason.lower() or "sangat pendek" in warnings_str.lower():
                dest_folder_rel = review_subfolders.get("possible_non_music", "90_NEEDS_REVIEW/POSSIBLE_NON_MUSIC")
            else:
                dest_folder_rel = review_subfolders.get("insufficient_data", "90_NEEDS_REVIEW/INSUFFICIENT_DATA")
            notes_reason = f"Confidence rendah ({confidence_score}/100) — {notes_reason}"

        # Tentukan direktori tujuan absolut
        dest_dir = os.path.join(final_output_dir, dest_folder_rel)
        os.makedirs(dest_dir, exist_ok=True)
        
        # Salin file ke folder tujuan akhir
        actual_final_path, copy_res = safe_copy_file(current_batch_path, dest_dir, filename)
        
        if copy_res == "SUCCESS":
            logger.debug(f"[{decision}] Sukses: {filename} → {dest_folder_rel}")
            sorting_row = {
                "source_path": current_batch_path,
                "target_path": actual_final_path,
                "old_filename": filename,
                "new_filename": os.path.basename(actual_final_path),
                "sorted_folder": dest_folder_rel,
                "confidence_score": confidence_score,
                "decision": decision,
                "status": "SUCCESS",
                "notes": notes_reason
            }
            batch_mgr.update_file_status(src_path, stage="sort", status="SUCCESS", target_path=actual_final_path)
            counts[decision] = counts.get(decision, 0) + 1
        else:
            logger.error(f"Gagal menyortir {filename} ke {dest_folder_rel}: {copy_res}")
            sorting_row = {
                "source_path": current_batch_path,
                "target_path": "",
                "old_filename": filename,
                "new_filename": filename,
                "sorted_folder": dest_folder_rel,
                "confidence_score": confidence_score,
                "decision": decision,
                "status": "FAILED",
                "notes": copy_res
            }
            batch_mgr.update_file_status(src_path, stage="sort", status="FAILED", error_msg=copy_res)
            counts["FAILED"] += 1
            
        sorting_records.append(sorting_row)
        
        processed_count += 1
        if processed_count % 50 == 0 or processed_count == len(target_records):
            logger.info(f"[SORT] Menyortir {processed_count}/{len(target_records)} berkas...")
    
    # Laporan ringkasan
    logger.info(f"[SORT] Hasil: AUTO_SORT={counts['AUTO_SORT']} | REVIEW_WITH_SUGGESTION={counts['REVIEW_WITH_SUGGESTION']} | NEEDS_REVIEW={counts['NEEDS_REVIEW']} | GAGAL={counts['FAILED']}")
            
    # Tulis laporan sortir
    csv_sorting_path = os.path.join(logs_dir, "folder_sorting_report.csv")
    xlsx_sorting_path = os.path.join(logs_dir, "folder_sorting_report.xlsx")
    
    write_csv_report(sorting_records, csv_sorting_path, SORT_COLUMNS)
    convert_csv_to_xlsx(csv_sorting_path, xlsx_sorting_path)
    
    logger.info(f"=== Sortir folder selesai. Laporan disimpan ke {csv_sorting_path} ===")
    return sorting_records

if __name__ == "__main__":
    setup_logger()
    sort_to_radio_folders(batch_id="TEST_BATCH")
