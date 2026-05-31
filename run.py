import os
import sys
import argparse
import logging
from datetime import datetime

from src.utils import setup_logger, load_json_config, import_module_by_path

# Impor pipeline utama secara dinamis untuk menghindari syntax error nama file numerik
run_full_pipeline = import_module_by_path("full_pipeline", "scripts/99_full_pipeline.py").run_full_pipeline

def show_welcome_banner():
    """Menampilkan banner pembuka di terminal."""
    banner = """
==================================================
        RADIO MUSIC CLEANER — Windows CLI
==================================================
Tool pembersihan & penataan library audio radio.
Menjaga file asli tetap aman dan utuh.
==================================================
"""
    print(banner)

def check_config_files() -> bool:
    """Memeriksa keberadaan file konfigurasi penting."""
    required_configs = [
        "config/cleaner_rules.json",
        "config/folder_mapping.json",
        "config/metadata_defaults.json",
        "config/batch_settings.json"
    ]
    for cfg in required_configs:
        if not os.path.exists(cfg):
            logging.error(f"Berkas konfigurasi penting tidak ditemukan: {cfg}")
            return False
    return True

def main():
    # Setup log utama
    logger = setup_logger()
    
    show_welcome_banner()
    
    # 1. Cek file konfigurasi terlebih dahulu
    if not check_config_files():
        logger.error("Gagal mendeteksi berkas konfigurasi. Hentikan eksekusi.")
        sys.exit(2) # Exit code 2: Config error

    # 2. Parsing argumen baris perintah
    parser = argparse.ArgumentParser(
        description="RADIO_MUSIC_CLEANER — Pembersihan dan penyusunan folder library audio secara aman.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    # Flag Operasi Aman (Dry-Run)
    parser.add_argument("--scan", action="store_true", help="Memindai folder input dan membuat laporan metadata audio.")
    parser.add_argument("--preview", action="store_true", help="Simulasi pembersihan nama file audio (dry-run).")
    parser.add_argument("--all-safe", action="store_true", help="Menjalankan scan, preview, deteksi duplikat, & QA (tanpa menulis file fisik).")
    
    # Flag Operasi Apply (Menulis/Mengubah data)
    parser.add_argument("--apply-rename", action="store_true", help="Menyalin file asli dan menerapkan nama file yang bersih ke folder batch.")
    parser.add_argument("--write-tags", action="store_true", help="Menulis tag metadata dasar (Artist/Title) ke file hasil salinan.")
    parser.add_argument("--sort", action="store_true", help="Menyortir file audio hasil bersih ke folder kategori radio akhir.")
    parser.add_argument("--duplicates", action="store_true", help="Mendeteksi duplikat dan menyalin file tersangka ke folder diduga duplikat.")
    parser.add_argument("--validate", action="store_true", help="Menjalankan audit kualitas QA pada library output final.")
    
    # Flag Kontrol Tambahan
    parser.add_argument("--resume", action="store_true", help="Melanjutkan proses batch yang terhenti berdasarkan status manifest.")
    parser.add_argument("--batch-id", type=str, default="", help="Menentukan ID batch secara manual. Jika kosong, dibuat otomatis.")
    
    args = parser.parse_args()
    
    # Jika tidak ada argumen sama sekali yang diberikan, tampilkan pesan bantuan
    if not len(sys.argv) > 1:
        parser.print_help()
        sys.exit(0)

    # 3. Tentukan ID Batch
    batch_id = args.batch_id
    if not batch_id:
        batch_id = f"BATCH_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    logger.info(f"Menggunakan ID Batch: {batch_id}")

    # 4. Validasi direktori input sebelum memulai
    batch_cfg = load_json_config("config/batch_settings.json", {})
    input_dir = batch_cfg.get("input_dir", "data/input")
    if not os.path.exists(input_dir) or not os.listdir(input_dir):
        logger.error(f"Folder input '{input_dir}' kosong atau tidak ditemukan! Letakkan file audio Anda di sana.")
        sys.exit(3) # Exit code 3: Input folder kosong

    # 5. Deteksi apakah ada operasi apply yang dijalankan
    is_apply_mode = args.apply_rename or args.write_tags or args.sort or args.duplicates
    
    if is_apply_mode:
        print("\n" + "!" * 55)
        print("PERINGATAN: ANDA AKAN MENULIS/MENYALIN FILE HASIL PROSES!")
        print("Proses ini akan memakan waktu dan ruang penyimpanan.")
        print("Tenang, file sumber asli Anda tidak akan diubah atau dihapus.")
        print("!" * 55)
        
        # Minta konfirmasi interaktif dari operator
        try:
            user_input = input("\nKetik YES untuk melanjutkan proses penulisan file: ").strip()
            if user_input != "YES":
                logger.warning("Operasi dibatalkan oleh pengguna.")
                sys.exit(4) # Exit code 4: Apply dibatalkan user
        except KeyboardInterrupt:
            print("\n")
            logger.warning("Operasi dibatalkan secara paksa.")
            sys.exit(4)
            
    # 6. Jalankan pipeline sesuai flag yang diaktifkan
    try:
        # Jika flag --all-safe aktif, jalankan semua mode aman
        if args.all_safe:
            logger.info("Menjalankan pipeline dalam mode aman (all-safe)...")
            run_full_pipeline(
                batch_id=batch_id,
                run_scan=True,
                run_preview=True,
                run_apply=False,
                run_metadata=False,
                run_sort=False,
                run_duplicates=True,
                run_validate=True,
                resume=args.resume
            )
        else:
            # Jalankan pipeline sesuai flag satuan
            run_full_pipeline(
                batch_id=batch_id,
                run_scan=args.scan or args.all_safe,
                run_preview=args.preview or args.all_safe,
                run_apply=args.apply_rename,
                run_metadata=args.write_tags,
                run_sort=args.sort,
                run_duplicates=args.duplicates or args.all_safe,
                run_validate=args.validate or args.all_safe,
                resume=args.resume
            )
            
        logger.info("Proses selesai dengan sukses!")
        sys.exit(0)
        
    except Exception as e:
        logger.critical(f"Terjadi kesalahan fatal pada sistem: {e}", exc_info=True)
        sys.exit(1) # Exit code 1: Error umum

if __name__ == "__main__":
    main()
