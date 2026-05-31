# RADIO_MUSIC_CLEANER

Aplikasi Command Line Interface (CLI) lokal Windows untuk memindai, membersihkan nama berkas, menulis metadata dasar, dan menyusun ribuan file audio/lagu siaran radio secara otomatis, aman, dan teratur.

## Fitur Utama

1. **Scan Library**: Memindai file audio di folder input dan mengekstrak info teknis serta tag metadatanya.
2. **Simulasi Preview (Dry-Run)**: Menampilkan rekomendasi nama berkas yang bersih sebelum pergantian nama fisik dilakukan.
3. **Pembersihan Nama Aman**: Menyalin file asli ke area kerja batch dan mengubah nama salinan tersebut. **File asli Anda di folder input dijamin tidak akan pernah diubah atau dihapus**.
4. **Penulisan Tag Dasar**: Mengisi tag Artist dan Title pada file hasil salinan secara otomatis berdasarkan pola nama file yang bersih.
5. **Penyusunan Folder**: Mengelompokkan berkas secara otomatis ke dalam struktur folder kategori radio akhir (Musik Indonesia, Dangdut, Religi, Musik Lokal Bugis/Makassar, Jingle, Iklan, dll.) berdasarkan analisis nama file dan tag.
6. **Deteksi Duplikat**: Mengidentifikasi dugaan file duplikat berdasarkan kemiripan nama, durasi, ukuran, dan tag, lalu mengumpulkannya di folder tersendiri untuk diaudit manual.
7. **Laporan Audit QA**: Memeriksa kualitas akhir library (keterbacaan audio, validitas nama file, dan kelayakan berkas On Air).
8. **Dashboard Analitik Interaktif**: Halaman visual berbasis web lokal (`dashboard.html`) yang menampilkan bagan interaktif, statistik library, dan tabel pencarian instan dari berkas laporan CSV Anda tanpa membutuhkan server.

---

## Persyaratan Sistem

- PC Windows 10 atau 11
- Python 3.7 ke atas

---

## Cara Instalasi

1. Pastikan Python 3 sudah terinstal di PC Anda. Jika belum, download di [python.org](https://www.python.org/downloads/) (centang opsi **Add Python to PATH** saat instalasi).
2. Buka terminal PowerShell atau Command Prompt (CMD) di folder proyek ini.
3. Instal dependensi pustaka yang dibutuhkan dengan menjalankan perintah:
   ```powershell
   pip install -r requirements.txt
   ```

---

## Panduan Penggunaan Operator

### 1. Memasukkan File Audio Sumber
Salin folder-folder audio yang berantakan milik radio Anda ke dalam direktori:
```text
data/input/
```

### 2. Memindai Library Audio
Gunakan perintah ini untuk memindai isi folder input dan membuat laporan:
```powershell
python run.py --scan
```
*Hasil Laporan:* `data/logs/audio_scan_report.xlsx`

### 3. Simulasi Pembersihan Nama (Preview)
Untuk melihat usulan nama file bersih yang diusulkan oleh sistem tanpa mengubah berkas fisik apa pun:
```powershell
python run.py --preview
```
*Hasil Laporan:* `data/logs/filename_cleaning_preview.xlsx`

### 4. Menerapkan Rename & Copy (Apply)
Untuk benar-benar membuat salinan file yang bersih dan rapi:
```powershell
python run.py --apply-rename
```
*Catatan:* Sistem akan meminta konfirmasi. Ketik `YES` untuk melanjutkan.  
*Hasil Salinan:* `data/output_batch/`  
*Laporan:* `data/logs/filename_cleaning_applied.csv`

### 5. Menulis Tag Metadata
Untuk mengisi metadata dasar (Artist & Title) pada file hasil salinan yang tag-nya kosong:
```powershell
python run.py --write-tags
```
*Hasil Laporan:* `data/logs/metadata_write_report.xlsx`

### 6. Menyortir File ke Folder Radio Kategori
Untuk menyusun berkas-berkas hasil pembersihan ke dalam struktur folder kategori radio akhir:
```powershell
python run.py --sort
```
*Hasil Library Final:* `data/output/RADIO_AUDIO_LIBRARY/`  
*Hasil Laporan:* `data/logs/folder_sorting_report.xlsx`

### 7. Mendeteksi File Duplikat
Untuk mendeteksi dugaan file ganda dan menyalinnya ke folder peninjauan manual:
```powershell
python run.py --duplicates
```
*Hasil Salinan Duplikat:* `data/duplikat_diduga/`  
*Hasil Laporan:* `data/logs/possible_duplicates_report.xlsx`

### 8. Audit Kualitas Validasi QA
Melakukan validasi akhir pada folder library final untuk memastikan tidak ada kesalahan nama file atau file corrupt:
```powershell
python run.py --validate
```
*Hasil Laporan:* `data/logs/output_validation_summary.md` & `output_validation_report.csv`

### 9. Visualisasi Interaktif via Dashboard Web
Untuk memantau data secara grafis dengan bagan dan tabel pencarian interaktif:
1. Buka berkas `dashboard.html` di browser Anda (cukup klik dua kali berkas tersebut).
2. Tarik (drag-and-drop) berkas `audio_scan_report.csv` atau `folder_sorting_report.csv` dari folder `data/logs/` ke area drop-zone di dashboard.
3. Dashboard akan langsung memvisualisasikan data track secara instan dan aman.

### 10. Fitur Resume Proses
Jika proses batch terhenti di tengah jalan karena listrik padam atau sebab lain, lanjutkan proses dengan menambahkan flag `--resume`:
```powershell
python run.py --apply-rename --resume
```

---

## Prinsip Keamanan Data

> [!WARNING]
> 1. **JANGAN UBAH FILE ASLI**: Sistem ini hanya membaca file asli di `data/input`. Semua hasil modifikasi berada di folder `data/output/`.
> 2. **TIDAK MENGHAPUS BERKAS**: Sistem tidak memiliki fungsi penghapusan otomatis untuk file duplikat atau corrupt guna mencegah hilangnya data penting. Anda harus menghapusnya secara manual berdasarkan laporan yang diterbitkan.
