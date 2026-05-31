import os
import sys
import argparse
import logging
from datetime import datetime

from src.utils import setup_logger, load_json_config, import_module_by_path

# Impor pipeline utama secara dinamis untuk menghindari syntax error nama file numerik
run_full_pipeline = import_module_by_path("full_pipeline", "scripts/99_full_pipeline.py").run_full_pipeline
build_index_catalog = import_module_by_path("build_index_catalog", "scripts/12_build_index_catalog.py").main
export_playlists = import_module_by_path("export_playlists", "scripts/13_export_playlists.py").main
run_classification_audit = import_module_by_path("run_classification_audit", "scripts/09_classify_and_report.py").run_classification_audit

fingerprint_candidates = import_module_by_path("fingerprint_candidates", "scripts/08_fingerprint_candidates.py").fingerprint_candidates
generate_metadata_suggestions = import_module_by_path("generate_metadata_suggestions", "scripts/09_generate_metadata_suggestions.py").evaluate_metadata_suggestions
build_review_queue = import_module_by_path("build_review_queue", "scripts/10_build_review_queue.py").build_review_queue_draft
apply_approved = import_module_by_path("apply_approved", "scripts/11_apply_approved_changes.py").apply_approved_changes

def show_welcome_banner():
    """Menampilkan banner pembuka di terminal stasiun radio."""
    banner = """
==================================================
      RADIO AUDIO LIBRARY MANAGER — Windows CLI v4.0
==================================================
Tool pembersihan, penataan, fingerprint AcoustID,
review queue, dan playlist creator library audio.
Menjaga file asli stasiun radio tetap aman & utuh.
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
    """Menampilkan antarmuka menu interaktif stasiun radio v4.0."""
    logger = logging.getLogger("RADIO_MUSIC_CLEANER")
    batch_id = f"BATCH_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Ambil konfigurasi default
    batch_cfg = load_json_config("config/batch_settings.json", {})
    default_input = batch_cfg.get("input_dir", "data/input")
    input_dir = default_input

    while True:
        print("\n" + "=" * 55)
        print("     MENU UTAMA RADIO AUDIO LIBRARY MANAGER v4.0")
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
        print(" 10. AcoustID Fingerprint Kandidat Lagu Resmi")
        print(" 11. Evaluasi Usulan Metadata AcoustID + MusicBrainz")
        print(" 12. Susun Draf Antrean Tinjauan Operator (Build Review Queue)")
        print(" 13. Eksekusi Persetujuan Perubahan Fisik (Apply Approved) *PROSES FISIK*")
        print(" 14. Bangun Katalog Master & Playlists M3U (Catalog Builder)")
        print(" 15. Ekspor Daftar Putar Siaran RadioBoss")
        print(" 16. Audit Klasifikasi Standalone (Classifier Audit)")
        print(" 17. Panduan Finishing (Mp3tag & MusicBrainz Picard)")
        print(" 18. Keluar")
        print("=" * 55)
        
        choice = input("Pilih menu (1-18): ").strip()
        
        # Muat ulang konfigurasi batch agar up-to-date
        batch_cfg2 = load_json_config("config/batch_settings.json", {})
        final_out = batch_cfg2.get("final_output_dir", "data/output/RADIO_AUDIO_MASTER_LIBRARY")
        logs = batch_cfg2.get("logs_dir", "data/logs")

        if choice == "1":
            new_path = input(f"\nMasukkan path folder musik baru\n(Enter untuk batal, default: '{input_dir}'): ").strip()
            if new_path:
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
            print("\n[INFO] Menjalankan AcoustID fingerprinting pada kandidat musik...")
            fingerprint_candidates(batch_id=batch_id, logs_dir=logs)
        elif choice == "11":
            print("\n[INFO] Menjalankan evaluasi usulan metadata AcoustID + MusicBrainz...")
            generate_metadata_suggestions(logs_dir=logs)
        elif choice == "12":
            print("\n[INFO] Menyusun draf antrean tinjauan operator (review queue)...")
            build_review_queue(logs_dir=logs)
        elif choice == "13":
            print("\n" + "!" * 55)
            print("PERINGATAN: ANDA AKAN MENGEKSEKUSI PERUBAHAN FISIK YANG DI-APPROVE!")
            print("Perubahan nama berkas dan penulisan tag akan diterapkan ke disk.")
            print("!" * 55)
            confirm = input("Ketik YES untuk mengeksekusi apply approved: ").strip()
            if confirm == "YES":
                apply_approved(final_output_dir=final_out, logs_dir=logs)
            else:
                print("Operasi dibatalkan.")
        elif choice == "14":
            print("\n[INFO] Membangun katalog master radio dan playlist logis M3U...")
            result = build_index_catalog(final_output_dir=final_out, logs_dir=logs)
            print(f"[OK] Katalog master & playlist logis berhasil dibuat!")
            print(f"  - Total Lagu Terkatalog : {result.get('total_records', 0)}")
            print(f"  - Playlist M3U Diekspor : {sum(result.get('playlists_stats', {}).values())} file")
        elif choice == "15":
            print("\n[INFO] Mengekspor playlist siaran logis untuk RadioBoss...")
            stats = export_playlists(final_output_dir=final_out, logs_dir=logs)
            print(f"[OK] Playlist RadioBoss sukses diekspor! Statistik: {stats}")
        elif choice == "16":
            print("\n[INFO] Menjalankan audit klasifikasi standalone...")
            run_classification_audit(input_dir=input_dir, logs_dir=logs)
            print("[OK] Audit klasifikasi standalone selesai!")
        elif choice == "17":
            print("\n" + "=" * 55)
            print("   PANDUAN INTEGRASI MP3TAG & MUSICBRAINZ PICARD")
            print("=" * 55)
            print("Setelah RADIO_MUSIC_CLEANER merapikan file dan folder,")
            print("Anda dapat menggunakan tool gratis berikut untuk finishing:")
            print("\n1. Mp3tag (Untuk Edit Tag & Gambar Album Massal)")
            print("   - Unduh gratis di: https://www.mp3tag.de/en/download.html")
            print("   - Cara pakai: Buka Mp3tag, masukkan folder output:")
            print("     'data/output/RADIO_AUDIO_MASTER_LIBRARY/'")
            print("   - Blok lagu, isi Album/Genre secara massal di panel kiri.")
            print("   - Tekan Ctrl + S untuk menyimpan.")
            print("\n2. MusicBrainz Picard (Untuk Auto-Tag lewat Sidik Jari Suara)")
            print("   - Unduh gratis di: https://picard.musicbrainz.org/")
            print("   - Sangat cocok untuk file bernama 'Track 01' atau 'Unknown'.")
            print("   - Cara pakai: Masukkan file, klik 'Scan' di menu atas.")
            print("   - Picard akan mendengarkan suara lagu dan mencarinya di database.")
            print("   - Klik kanan album di kolom kanan -> Save (Ctrl + S).")
            print("=" * 55)
        elif choice == "18":
            print("\nTerima kasih telah menggunakan RADIO AUDIO LIBRARY MANAGER. Sampai jumpa!\n")
            break
        else:
            print("\n[ERROR] Pilihan tidak valid. Silakan pilih nomor 1-18.")
            
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
        description="RADIO AUDIO LIBRARY MANAGER v4.0 — Pembersihan dan penyusunan folder stasiun radio secara aman.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    # Flag Operasi Aman (Dry-Run / Mode Analisa)
    parser.add_argument("--scan", action="store_true", help="Memindai folder input dan membuat laporan metadata audio.")
    parser.add_argument("--preview", action="store_true", help="Simulasi pembersihan nama file audio (dry-run).")
    parser.add_argument("--all-safe", action="store_true", help="Menjalankan scan, preview, classify, review queue draft, & summary (mode aman).")
    parser.add_argument("--classify", action="store_true", help="Menjalankan audit klasifikasi standalone tanpa menyalin file fisik.")
    parser.add_argument("--fingerprint-candidates", action="store_true", help="Menjalankan AcoustID fingerprinting pada berkas lagu layak.")
    parser.add_argument("--metadata-suggestions", action="store_true", help="Mengevaluasi usulan metadata sidik jari AcoustID + MusicBrainz.")
    parser.add_argument("--build-review-queue", action="store_true", help="Menyusun antrean tinjauan operator (review queue).")
    
    # Flag Operasi Apply (Menulis/Mengubah data fisik)
    parser.add_argument("--apply-rename", action="store_true", help="Menyalin file asli dan menerapkan nama file yang bersih ke folder batch.")
    parser.add_argument("--write-tags", action="store_true", help="Menulis tag metadata dasar (Artist/Title) ke file hasil salinan.")
    parser.add_argument("--sort", action="store_true", help="Menyortir file audio hasil bersih ke folder kategori radio akhir.")
    parser.add_argument("--duplicates", action="store_true", help="Mendeteksi duplikat dan menyalin file tersangka ke folder diduga duplikat.")
    parser.add_argument("--validate", action="store_true", help="Menjalankan audit kualitas QA pada library output final.")
    parser.add_argument("--apply-approved", action="store_true", help="Menerapkan perubahan nama berkas dan tag yang disetujui operator.")
    parser.add_argument("--build-index", action="store_true", help="Membangun katalog master radio secara dinamis.")
    parser.add_argument("--export-playlists", action="store_true", help="Mengekspor playlist pointer logis M3U untuk siaran RadioBoss.")
    
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
    is_apply_mode = args.apply_rename or args.write_tags or args.sort or args.duplicates or args.apply_approved
    
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
        if args.classify:
            logger.info("Menjalankan audit klasifikasi standalone...")
            run_classification_audit(input_dir=input_dir, logs_dir="data/logs")
            logger.info("Audit klasifikasi standalone selesai!")
            sys.exit(0)

        # Jika flag --all-safe aktif, jalankan semua mode aman (dry-run v4.0 lengkap)
        if args.all_safe:
            logger.info("Menjalankan pipeline dalam mode aman (all-safe) v4.0...")
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
                run_fingerprint=True,
                run_suggestions=True,
                run_review=True,
                run_apply_approved=False,
                run_index=True,
                run_playlists=False,
                resume=args.resume
            )
        else:
            # Jalankan pipeline sesuai flag satuan
            run_full_pipeline(
                batch_id=batch_id,
                input_dir=input_dir,
                run_scan=args.scan,
                run_preview=args.preview,
                run_apply=args.apply_rename,
                run_metadata=args.write_tags,
                run_sort=args.sort,
                run_duplicates=args.duplicates,
                run_validate=args.validate,
                run_fingerprint=args.fingerprint_candidates,
                run_suggestions=args.metadata_suggestions,
                run_review=args.build_review_queue,
                run_apply_approved=args.apply_approved,
                run_index=args.build_index,
                run_playlists=args.export_playlists,
                resume=args.resume
            )
            
        logger.info("Proses selesai dengan sukses!")
        sys.exit(0)
        
    except Exception as e:
        logger.critical(f"Terjadi kesalahan fatal pada sistem: {e}", exc_info=True)
        sys.exit(1) # Exit code 1: Error umum

if __name__ == "__main__":
    main()
