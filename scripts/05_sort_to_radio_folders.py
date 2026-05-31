import os
import csv
import logging
import shutil
from typing import List, Dict, Any

from src.utils import load_json_config, setup_logger
from src.folder_sorter import determine_target_folder
from src.safe_file_ops import safe_copy_file, make_windows_safe_path
from src.batch_manager import BatchManager
from src.report_writer import write_csv_report, convert_csv_to_xlsx

# Kolom untuk laporan sortir folder
SORT_COLUMNS = [
    "source_path", "target_path", "old_filename", "new_filename", 
    "sorted_folder", "status", "notes"
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
    
    # 2. Muat konfigurasi mapping folder
    folder_mapping = load_json_config("config/folder_mapping.json", {})
    
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
    for row in target_records:
        src_path = row.get("source_path") # Path file asli
        current_batch_path = row.get("target_path") # Path file bersih sementara di output_batch
        
        # Validasi path fisik file sementara
        if not current_batch_path or not os.path.exists(current_batch_path):
            logger.warning(f"File sementara di output_batch tidak ditemukan: {current_batch_path}")
            continue
            
        # Cek resume
        if resume and row.get("sort_status") == "SUCCESS":
            logger.info(f"Resume: Skip sortir untuk {os.path.basename(current_batch_path)}")
            # Masukkan info dummy/lama untuk konsistensi laporan
            sorting_records.append({
                "source_path": current_batch_path,
                "target_path": row.get("target_path"), # dummy
                "old_filename": os.path.basename(current_batch_path),
                "new_filename": os.path.basename(current_batch_path),
                "sorted_folder": "",
                "status": "SKIPPED",
                "notes": "Dilewati karena sudah selesai pada sesi sebelumnya (Resume)"
            })
            continue

        # Dapatkan data usulan folder
        scan_info = scan_data_map.get(src_path, {})
        suggested_folder = scan_info.get("suggested_folder", "")
        
        # Jika usulan folder tidak ada, tentukan ulang
        if not suggested_folder:
            filename = os.path.basename(current_batch_path)
            suggested_folder, _ = determine_target_folder(
                filename, genre_tag="", artist_tag="", title_tag="", mapping_config=folder_mapping
            )
            
        # Tentukan direktori tujuan absolut
        dest_dir = os.path.join(final_output_dir, suggested_folder)
        filename = os.path.basename(current_batch_path)
        
        # Salin file dari folder batch sementara ke folder tujuan akhir
        # (Kita gunakan penyalinan aman agar tidak menimpa jika nama file bentrok di folder tujuan)
        actual_final_path, copy_res = safe_copy_file(current_batch_path, dest_dir, filename)
        
        if copy_res == "SUCCESS":
            logger.debug(f"Sukses menyortir: {filename} -> {suggested_folder}")
            sorting_row = {
                "source_path": current_batch_path,
                "target_path": actual_final_path,
                "old_filename": filename,
                "new_filename": os.path.basename(actual_final_path),
                "sorted_folder": suggested_folder,
                "status": "SUCCESS",
                "notes": f"Disortir ke {suggested_folder}"
            }
            batch_mgr.update_file_status(src_path, stage="sort", status="SUCCESS", target_path=actual_final_path)
            
            # Jika penyalinan sukses dan file sementara ada di output_batch, 
            # kita bisa menghapus file sementara untuk menghemat ruang, 
            # NAMUN hanya jika setting allow_delete aktif atau secara default kita biarkan 
            # agar operator mengosongkan manual (seperti dijelaskan di grand design).
            # Kita biarkan file sementara tetap ada sebagai cadangan aman, 
            # kecuali dikonfigurasi lain.
        else:
            logger.error(f"Gagal menyortir {filename} ke {suggested_folder}: {copy_res}")
            sorting_row = {
                "source_path": current_batch_path,
                "target_path": "",
                "old_filename": filename,
                "new_filename": filename,
                "sorted_folder": suggested_folder,
                "status": "FAILED",
                "notes": copy_res
            }
            batch_mgr.update_file_status(src_path, stage="sort", status="FAILED", error_msg=copy_res)
            
        sorting_records.append(sorting_row)
        
        processed_count += 1
        if processed_count % 50 == 0 or processed_count == len(target_records):
            logger.info(f"[SORT] Menyortir {processed_count}/{len(target_records)} berkas...")
            
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
