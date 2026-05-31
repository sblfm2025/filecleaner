# 04 — Desain Batch Processing untuk Ratusan GB

## 1. Masalah Utama

Library audio radio bisa berukuran:

```text
100 GB
300 GB
500 GB
1 TB
```

Sistem tidak boleh memuat semua file ke RAM sekaligus.

Yang berat bukan hanya ukuran GB, tetapi:

- jumlah file,
- kondisi HDD/SSD,
- file corrupt,
- metadata rusak,
- copy antar drive,
- laporan besar,
- path panjang Windows,
- proses metadata satu per satu.

## 2. Prinsip Desain

Sistem harus menggunakan pola:

```text
iterator/generator
proses satu file per satu
log per file
resume process
batch_id
checkpoint
skip file selesai
```

Dilarang:

```text
load semua file ke list besar tanpa perlu
menyimpan semua metadata di RAM untuk ratusan ribu file
mengubah file asli
menghapus file otomatis
overwrite output
```

## 3. Ukuran Batch

Rekomendasi:

```text
Uji coba awal : 20–50 file
Batch kecil   : 5–10 GB
Batch normal  : 30–50 GB
Batch besar   : 100 GB jika PC kuat
```

Untuk PC standar, gunakan batch 30–50 GB.

## 4. Struktur Batch

Gunakan folder:

```text
data/input_batch/
data/output_batch/
data/logs/batches/
```

Setiap batch punya ID:

```text
BATCH_20260531_001
BATCH_20260531_002
BATCH_20260531_003
```

Laporan per batch:

```text
data/logs/batches/BATCH_20260531_001_scan.csv
data/logs/batches/BATCH_20260531_001_preview.csv
data/logs/batches/BATCH_20260531_001_metadata.csv
data/logs/batches/BATCH_20260531_001_sorting.csv
data/logs/batches/BATCH_20260531_001_summary.md
```

## 5. batch_settings.json

Buat:

```json
{
  "batch_mode": true,
  "batch_id_prefix": "BATCH",
  "max_batch_size_gb": 50,
  "max_files_per_batch": 5000,
  "input_batch_dir": "data/input_batch",
  "output_batch_dir": "data/output_batch",
  "final_output_dir": "data/output/RADIO_AUDIO_LIBRARY",
  "logs_dir": "data/logs",
  "resume_enabled": true,
  "skip_completed_files": true,
  "dry_run_default": true
}
```

## 6. Resume Process

Setiap file wajib dicatat dalam manifest:

```text
data/logs/process_manifest.csv
```

Kolom:

```text
batch_id
file_id
source_path
source_size
source_modified_time
current_stage
scan_status
rename_status
metadata_status
sort_status
duplicate_status
target_path
error_message
processed_at
```

Jika proses berhenti, sistem membaca manifest dan melanjutkan dari file yang belum selesai.

## 7. Status Per File

Gunakan status standar:

```text
PENDING
SCANNED
PREVIEWED
COPIED
RENAMED
METADATA_WRITTEN
SORTED
DUPLICATE_SUSPECT
NEEDS_REVIEW
ERROR
SKIPPED
DONE
```

## 8. Checkpoint

Setelah memproses setiap file, tulis status ke log.

Jangan menunggu sampai semua file selesai baru menulis laporan.

Untuk CSV besar, gunakan mode append.

Untuk XLSX, boleh dibuat di akhir dari CSV.

## 9. Memory Safe Reporting

Untuk batch besar:

- tulis CSV bertahap,
- hindari DataFrame raksasa jika file sangat banyak,
- jika menggunakan pandas, gunakan per batch,
- gabungkan laporan di akhir jika perlu.

## 10. Copy Aman

Gunakan `shutil.copy2`, bukan move.

Aturan:

```text
input_batch -> output_batch -> final_output
```

File asli di luar project tidak disentuh.

## 11. Cleanup Batch

Setelah batch selesai dan operator sudah cek hasil:

- output final dipindahkan/merge ke `RADIO_AUDIO_LIBRARY`,
- input_batch boleh dikosongkan manual,
- output_batch boleh dikosongkan manual,
- log batch tetap disimpan.

Sistem tidak boleh menghapus otomatis tanpa flag eksplisit.

## 12. Estimasi Storage

Jika batch 50 GB:

```text
input_batch  : 50 GB
output_batch : 50 GB
cadangan     : 10–20 GB
total kosong : ±120 GB
```

Jika batch 100 GB:

```text
input_batch  : 100 GB
output_batch : 100 GB
cadangan     : 20–30 GB
total kosong : ±230 GB
```

## 13. Kriteria Aman untuk Ratusan GB

Sistem dianggap siap memproses ratusan GB jika:

- berhasil uji 50 file,
- berhasil uji 5 GB,
- berhasil uji 50 GB,
- resume berhasil setelah proses dihentikan paksa,
- tidak ada file asli berubah,
- log lengkap,
- output tidak overwrite,
- file error tidak menghentikan batch,
- hasil preview masuk akal.
