# Panduan Operator Windows — RADIO_MUSIC_CLEANER

Dokumen ini ditujukan bagi operator non-teknis radio publik lokal untuk mengoperasikan tool pembersih library lagu secara mandiri di PC Windows.

---

## Langkah 1: Persiapan Awal
1. Buka folder proyek **RADIO_MUSIC_CLEANER** di PC Anda.
2. Temukan folder bernama `data/input`. Jika belum ada, jalankan perintah scan terlebih dahulu untuk membuatnya otomatis.
3. Salin file atau folder musik Anda yang berantakan ke dalam folder `data/input` tersebut.
   > [!IMPORTANT]
   > Harap gunakan file **salinan** saja di folder `data/input`. Simpan file master utama Anda di tempat yang aman (harddisk eksternal atau folder lain) sebagai cadangan.

---

## Langkah 2: Membuka Command Line (Terminal)
1. Buka folder proyek di Windows Explorer.
2. Klik pada area kosong di kolom alamat (Address Bar) di bagian atas, lalu ketik `cmd` atau `powershell` dan tekan tombol **Enter**.
3. Jendela hitam Command Prompt atau biru PowerShell akan terbuka, mengarah langsung ke folder proyek.

---

## Langkah 3: Menjalankan Audit Awal (Dry-Run / Aman)
Sebelum benar-benar memproses file secara nyata, Anda wajib menjalankan audit aman.
1. **Pindai Isi Folder**:
   ```powershell
   python run.py --scan
   ```
   Tunggu hingga proses selesai. Sistem akan membuat laporan file audio di `data/logs/audio_scan_report.xlsx`. Anda bisa membukanya dengan Excel untuk melihat metadata lagu Anda saat ini.
2. **Preview Hasil Pembersihan Nama**:
   ```powershell
   python run.py --preview
   ```
   Sistem akan mensimulasikan pembersihan nama file (menghapus kata `Official Video`, `Lirik`, dll.) ke dalam file `data/logs/filename_cleaning_preview.xlsx`. Buka laporan tersebut untuk mengecek apakah nama lagu baru yang diusulkan sudah rapi.

---

## Langkah 4: Eksekusi Penataan (Apply)
Jika Anda sudah puas dengan laporan preview, mari lakukan pemrosesan fisik secara bertahap.

1. **Buat Salinan dengan Nama Bersih**:
   ```powershell
   python run.py --apply-rename
   ```
   *Penting:* Konsol akan memunculkan peringatan keamanan. Ketik **`YES`** dan tekan **Enter** untuk melanjutkan. Sistem akan menyalin file Anda ke `data/output_batch/` dengan nama baru yang bersih.
   
2. **Isi Metadata Otomatis**:
   ```powershell
   python run.py --write-tags
   ```
   Ketik **`YES`** saat konfirmasi. Perintah ini akan mengisi tag Artist dan Title pada file hasil salinan yang metadatanya masih kosong berdasarkan nama file baru yang rapi.
   
3. **Penyusunan Folder Otomatis**:
   ```powershell
   python run.py --sort
   ```
   Ketik **`YES`** saat konfirmasi. Sistem akan memindahkan file-file dari folder batch sementara ke struktur folder kategori penyiaran radio di dalam:
   ```text
   data/output/RADIO_AUDIO_LIBRARY/
   ```

---

## Langkah 5: Penanganan File Duplikat
1. Jalankan perintah deteksi duplikat:
   ```powershell
   python run.py --duplicates
   ```
2. Sistem akan menandai file yang dicurigai sebagai file ganda dan menyalinnya ke folder `data/duplikat_diduga/` untuk ditinjau.
3. Buka file laporan `data/logs/possible_duplicates_report.xlsx` untuk melihat perbandingan durasi, ukuran, dan nama file yang dicurigai duplikat. Anda dapat menghapus file duplikat yang benar-benar tidak dibutuhkan secara manual dari folder library final.

---

## Langkah 6: Validasi Akhir (QA Check)
1. Jalankan perintah validasi kualitas:
   ```powershell
   python run.py --validate
   ```
2. Buka laporan ringkasan `data/logs/output_validation_summary.md` dan file CSV `data/logs/output_validation_report.csv` untuk memastikan tidak ada kesalahan nama file, file corrupt, atau file di folder `00_ON_AIR_READY` yang metadatanya belum lengkap.

---

## Langkah 7: Pemantauan Visual via Dashboard Web
Untuk mempermudah pemantauan statistik dan visualisasi lagu secara interaktif tanpa repot membuka berkas Excel:
1. Buka berkas `dashboard.html` di browser Google Chrome, Microsoft Edge, atau Firefox Anda (klik dua kali berkas tersebut di folder proyek).
2. Tarik berkas `audio_scan_report.csv` atau `folder_sorting_report.csv` dari folder `data/logs/` dan lepaskan di area kotak putus-putus abu-abu di halaman dashboard.
3. Anda akan disuguhi grafik lingkaran status track, grafik batang pembagian kategori, serta tabel pencarian interaktif untuk menyaring lagu bermasalah atau lagu tertentu secara instan.
