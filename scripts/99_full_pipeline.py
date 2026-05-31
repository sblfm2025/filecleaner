import os
import logging
from datetime import datetime
from typing import Dict, Any

from src.utils import load_json_config, setup_logger, import_module_by_path
from src.report_writer import write_final_summary_md
from src.batch_manager import BatchManager

# Impor modul langkah pipeline secara dinamis untuk menghindari syntax error nama file diawali angka
scan_audio_library = import_module_by_path("scan_audio_library", "scripts/01_scan_audio_library.py").scan_audio_library
clean_filename_preview = import_module_by_path("clean_filename_preview", "scripts/02_clean_filename_preview.py").clean_filename_preview
apply_filename_cleaning = import_module_by_path("apply_filename_cleaning", "scripts/03_apply_filename_cleaning.py").apply_filename_cleaning
write_basic_metadata_to_batch = import_module_by_path("write_basic_metadata", "scripts/04_write_basic_metadata.py").write_basic_metadata_to_batch
sort_to_radio_folders = import_module_by_path("sort_to_radio_folders", "scripts/05_sort_to_radio_folders.py").sort_to_radio_folders
detect_possible_duplicates = import_module_by_path("detect_possible_duplicates", "scripts/06_detect_possible_duplicates.py").detect_possible_duplicates
validate_output_library = import_module_by_path("validate_output_library", "scripts/07_validate_output_library.py").validate_output_library
build_index_catalog = import_module_by_path("build_index_catalog", "scripts/08_build_index_catalog.py").main

def run_full_pipeline(
    batch_id: str = "",
    input_dir: str = "",
    run_scan: bool = False,
    run_preview: bool = False,
    run_apply: bool = False,
    run_metadata: bool = False,
    run_sort: bool = False,
    run_duplicates: bool = False,
    run_validate: bool = False,
    run_index: bool = False,
    resume: bool = False
) -> None:
    """
    Menjalankan alur lengkap (pipeline) pemrosesan library audio radio.
    Mengintegrasikan scan, preview, rename, metadata, sortir, duplikat, dan validasi.
    """
    logger = logging.getLogger("RADIO_MUSIC_CLEANER")
    
    # 1. Pastikan ID batch siap
    if not batch_id:
        batch_id = f"BATCH_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    logger.info(f"==================================================")
    logger.info(f"MENJALANKAN PIPELINE UTAMA — ID BATCH: {batch_id}")
    logger.info(f"==================================================")
    
    # Load konfigurasi batch
    batch_cfg = load_json_config("config/batch_settings.json", {})
    input_dir_cfg = batch_cfg.get("input_dir", "data/input")
    input_dir = input_dir if input_dir else input_dir_cfg
    output_batch_dir = batch_cfg.get("output_batch_dir", "data/output_batch")
    final_output_dir = batch_cfg.get("final_output_dir", "data/output/RADIO_AUDIO_MASTER_LIBRARY")
    logs_dir = batch_cfg.get("logs_dir", "data/logs")
    
    # Jalankan langkah-langkah yang diaktifkan
    scan_results = []
    preview_results = []
    apply_results = []
    metadata_results = []
    sort_results = []
    duplicate_results = []
    validation_results = []
    
    # A. SCAN LIBRARY
    if run_scan:
        scan_results = scan_audio_library(
            batch_id=batch_id,
            input_dir=input_dir,
            logs_dir=logs_dir,
            resume=resume
        )
        
    # B. PREVIEW RENAME
    if run_preview:
        preview_results = clean_filename_preview(
            batch_id=batch_id,
            input_dir=input_dir,
            logs_dir=logs_dir
        )
        
    # C. APPLY RENAME (MENYALIN & RENAME AMAN)
    if run_apply:
        apply_results = apply_filename_cleaning(
            batch_id=batch_id,
            output_batch_dir=output_batch_dir,
            logs_dir=logs_dir,
            resume=resume
        )
        
    # D. WRITE METADATA
    if run_metadata:
        metadata_results = write_basic_metadata_to_batch(
            batch_id=batch_id,
            logs_dir=logs_dir,
            resume=resume
        )
        
    # E. SORTIR KATEGORI FOLDER
    if run_sort:
        sort_results = sort_to_radio_folders(
            batch_id=batch_id,
            final_output_dir=final_output_dir,
            logs_dir=logs_dir,
            resume=resume
        )
        
    # F. DETEKSI DUPLIKAT
    if run_duplicates:
        # Tentukan folder diduga duplikat dari mapping atau default
        folder_mapping = load_json_config("config/folder_mapping.json", {})
        dup_folder_rel = folder_mapping.get("duplicate_folder", "91_DUPLIKAT_DIDUGA")
        dup_folder_abs = os.path.join(final_output_dir, dup_folder_rel)
        
        duplicate_results = detect_possible_duplicates(
            batch_id=batch_id,
            final_output_dir=final_output_dir,
            logs_dir=logs_dir,
            duplicate_dest_dir=dup_folder_abs
        )
        
    # G. VALIDASI KUALITAS QA
    if run_validate:
        validation_results = validate_output_library(
            batch_id=batch_id,
            final_output_dir=final_output_dir,
            logs_dir=logs_dir
        )

    # H. BUILD INDEX & PLAYLIST CATALOG v3.0
    if run_index:
        build_index_catalog(
            final_output_dir=final_output_dir,
            logs_dir=logs_dir
        )

    # 2. Susun Statistik untuk Laporan Summary Eksekutif
    batch_mgr = BatchManager(logs_dir)
    batch_records = batch_mgr.get_all_records_for_batch(batch_id)
    
    total_files = len(scan_results) if scan_results else len(batch_records)
    total_audio = total_files # Karena scanner hanya memasukkan file audio
    
    # Hitung data riil dari manifest
    scanned_success = sum(1 for r in batch_records if r.get("scan_status") == "SUCCESS")
    scanned_error = sum(1 for r in batch_records if r.get("scan_status") in ["FAILED", "ERROR"])
    renamed_success = sum(1 for r in batch_records if r.get("rename_status") == "SUCCESS")
    metadata_written = sum(1 for r in batch_records if r.get("metadata_status") == "SUCCESS")
    sorted_success = sum(1 for r in batch_records if r.get("sort_status") == "SUCCESS")
    
    # Hitung jumlah file review & duplikat
    needs_review_count = 0
    for r in batch_records:
        target_path = r.get("target_path", "")
        if target_path and "90_NEEDS_REVIEW" in target_path:
            needs_review_count += 1
            
    bad_audio_count = scanned_error
    duplicates_count = len(duplicate_results)
    
    # Mode eksekusi
    execution_mode = "DRY_RUN (Simulasi)"
    if run_apply or run_metadata or run_sort:
        execution_mode = "APPLY (Menulis File)"
        
    summary_data = {
        "batch_id": batch_id,
        "processed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "execution_mode": execution_mode,
        "total_files": total_files,
        "total_audio": total_audio,
        "scanned_success": scanned_success,
        "scanned_error": scanned_error,
        "renamed_success": renamed_success,
        "metadata_written": metadata_written,
        "sorted_success": sorted_success,
        "needs_review": needs_review_count,
        "duplicates_suspect": duplicates_count,
        "bad_audio": bad_audio_count,
        
        # Lokasi berkas laporan
        "output_library_path": final_output_dir,
        "scan_report_path": os.path.join(logs_dir, "audio_scan_report.csv"),
        "preview_report_path": os.path.join(logs_dir, "filename_cleaning_preview.csv"),
        "metadata_report_path": os.path.join(logs_dir, "metadata_write_report.csv"),
        "sorting_report_path": os.path.join(logs_dir, "folder_sorting_report.csv"),
        "duplicates_report_path": os.path.join(logs_dir, "possible_duplicates_report.csv"),
        "validation_report_path": os.path.join(logs_dir, "output_validation_report.csv"),
        
        "needs_review_folder_name": "90_NEEDS_REVIEW",
        "duplicates_report_name": "possible_duplicates_report.csv"
    }
    
    # Tulis summary Markdown
    summary_path = os.path.join(logs_dir, "final_summary.md")
    write_final_summary_md(summary_data, summary_path)
    
    logger.info("=== Pipeline Utama Selesai ===")
    logger.info(f"Laporan ringkasan eksekutif disimpan ke: {summary_path}")
    
if __name__ == "__main__":
    setup_logger()
    run_full_pipeline(
        batch_id="TEST_PIPELINE",
        run_scan=True,
        run_preview=True,
        run_apply=False,
        run_metadata=False,
        run_sort=False,
        run_duplicates=True,
        run_validate=True,
        run_index=True
    )
