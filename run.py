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

def interactive_menu():
    """Menampilkan antarmuka menu interaktif yang mudah digunakan tanpa perlu mengingat perintah CLI."""
    logger = logging.getLogger("RADIO_MUSIC_CLEANER")
    batch_id = f"BATCH_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Ambil konfigurasi default
    batch_cfg = load_json_config("config/batch_settings.json", {})
    default_input = batch_cfg.get("input_dir", "data/input")
    input_dir = default_input

    while True:
        print("\n" + "=" * 55)
        print("          MENU UTAMA RADIO_MUSIC_CLEANER")
        print("=" * 55)
        print(f" Folder Input Aktif: {input_dir}")
        print(f" ID Batch Aktif    : {batch_id}")
        print("-" * 55)
        print(" 1. Ubah Folder Input Lagu")
        print(" 2. Pindai Folder Musik & Baca Metadata (Scan)")
        print(" 3. Lihat Simulasi Pembersihan Nama Berkas (Preview)")
        print(" 4. Jalankan Audit Mode Aman (Scan + Preview + Duplikat + QA)")
        print(" 5. Salin & Bersihkan Nama File (Apply Rename)  *PROSES FISIK*")
        print(" 6. Tulis Tag Metadata Dasar (Write Tags)       *PROSES FISIK*")
        print(" 7. Susun File ke Folder Kategori (Sort)        *PROSES FISIK*")
        print(" 8. Deteksi & Kumpulkan Berkas Duplikat (Duplicates)")
        print(" 9. Audit Validasi Kualitas Library Akhir (Validate)")
        print(" 10. Keluar")
        print("=" * 55)
        
        choice = input("Pilih menu (1-10): ").strip()
        
        if choice == "1":
            new_path = input(f"\nMasukkan path folder musik baru\n(Enter untuk batal, default: '{input_dir}'): ").strip()
            if new_path:
                # Bersihkan tanda kutip jika operator melakukan drag-drop folder ke terminal
                new_path = new_path.replace('"', '').replace("'", "")
                if os.path.exists(new_path):
                    input_dir = new_path
                    print(f"\n[OK] Folder input berhasil diubah ke: {input_dir}")
                else:
                    print(f"\n[ERROR] Folder '{new_path}' tidak ditemukan di disk!")
        elif choice == "2":
            run_full_pipeline(batch_id=batch_id, input_dir=input_dir, run_scan=True)
        elif choice == "3":
            run_full_pipeline(batch_id=batch_id, input_dir=input_dir, run_preview=True)
        elif choice == "4":
            run_full_pipeline(batch_id=batch_id, input_dir=input_dir, run_scan=True, run_preview=True, run_duplicates=True, run_validate=True)
        elif choice == "5":
            print("\n" + "!" * 55)
            print("PERINGATAN: ANDA AKAN MENYALIN & MERAPIKAN NAMA BERKAS!")
            print("File asli Anda dijamin tetap aman dan tidak akan diubah.")
            print("!" * 55)
            confirm = input("Ketik YES untuk melanjutkan proses: ").strip()
            if confirm == "YES":
                run_full_pipeline(batch_id=batch_id, input_dir=input_dir, run_apply=True)
            else:
                print("Operasi dibatalkan.")
        elif choice == "6":
            print("\n" + "!" * 55)
            print("PERINGATAN: TAG METADATA AKAN DITULIS KE FILE HASIL SALINAN!")
            print("!" * 55)
            confirm = input("Ketik YES untuk melanjutkan proses: ").strip()
            if confirm == "YES":
                run_full_pipeline(batch_id=batch_id, input_dir=input_dir, run_metadata=True)
            else:
                print("Operasi dibatalkan.")
        elif choice == "7":
            print("\n" + "!" * 55)
            print("PERINGATAN: BERKAS AKAN DISUSUN KE FOLDER KATEGORI RADIO!")
            print("!" * 55)
            confirm = input("Ketik YES untuk melanjutkan proses: ").strip()
            if confirm == "YES":
                run_full_pipeline(batch_id=batch_id, input_dir=input_dir, run_sort=True)
            else:
                print("Operasi dibatalkan.")
        elif choice == "8":
            run_full_pipeline(batch_id=batch_id, input_dir=input_dir, run_duplicates=True)
        elif choice == "9":
            run_full_pipeline(batch_id=batch_id, input_dir=input_dir, run_validate=True)
        elif choice == "10":
            print("\nTerima kasih telah menggunakan RADIO_MUSIC_CLEANER. Sampai jumpa!\n")
            break
        else:
            print("\n[ERROR] Pilihan tidak valid. Silakan pilih nomor 1-10.")
            
        input("\nTekan ENTER untuk kembali ke Menu Utama...")

def main():
    # Setup log utama
    logger = setup_logger()
    
    # Jika tidak ada argumen sama sekali, jalankan Menu Interaktif yang mudah dan compact
    if len(sys.argv) == 1:
        interactive_menu()
        sys.exit(0)
    
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
    parser.add_argument("-i", "--input-dir", type=str, default="", help="Path ke folder musik luar yang ingin dipindai langsung.")
    parser.add_argument("--resume", action="store_true", help="Melanjutkan proses batch yang terhenti berdasarkan status manifest.")
    parser.add_argument("--batch-id", type=str, default="", help="Menentukan ID batch secara manual. Jika kosong, dibuat otomatis.")
    
    args = parser.parse_args()

    # 3. Tentukan ID Batch
    batch_id = args.batch_id
    if not batch_id:
        batch_id = f"BATCH_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    logger.info(f"Menggunakan ID Batch: {batch_id}")

    # 4. Validasi direktori input sebelum memulai
    batch_cfg = load_json_config("config/batch_settings.json", {})
    input_dir = args.input_dir if args.input_dir else batch_cfg.get("input_dir", "data/input")
    if not os.path.exists(input_dir) or not os.listdir(input_dir):
        logger.error(f"Folder input '{input_dir}' kosong atau tidak ditemukan! Tentukan path folder yang benar.")
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
                input_dir=input_dir,
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
                input_dir=input_dir,
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
