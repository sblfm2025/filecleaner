# 06 — Spesifikasi Script Python

## 1. 01_scan_audio_library.py

### Tujuan

Memindai semua file audio di `data/input` atau `data/input_batch`.

### Ekstensi Audio

Minimal:

```text
.mp3
.wav
.flac
.m4a
.aac
.ogg
.wma
```

### Data yang dibaca

```text
id
batch_id
original_path
filename
extension
file_size_mb
modified_time
duration_seconds
duration_readable
bitrate
sample_rate
title_tag
artist_tag
album_tag
genre_tag
year_tag
clean_filename_suggestion
detected_artist_from_filename
detected_title_from_filename
suggested_folder
status
notes
```

### Output

```text
data/logs/audio_scan_report.csv
data/logs/audio_scan_report.xlsx
```

### Status

```text
OK
TAG_KOSONG
TITLE_KOSONG
ARTIST_KOSONG
NAMA_FILE_KOTOR
FORMAT_TIDAK_DIDUKUNG
AUDIO_ERROR
PERLU_DICEK
```

## 2. 02_clean_filename_preview.py

### Tujuan

Membuat simulasi pembersihan nama file tanpa mengubah file.

### Output

```text
data/logs/filename_cleaning_preview.csv
data/logs/filename_cleaning_preview.xlsx
```

### Kolom

```text
source_path
old_filename
new_filename_suggestion
detected_artist
detected_title
change_reason
safe_to_apply
notes
```

### Aturan

- tidak rename file,
- hanya preview,
- default wajib aman.

## 3. 03_apply_filename_cleaning.py

### Tujuan

Menerapkan rename pada salinan file.

### Prinsip

```text
copy2 dari input ke output
rename hasil copy
jangan ubah sumber asli
jangan overwrite
buat nama unik jika bentrok
```

### Output

```text
data/logs/filename_cleaning_applied.csv
```

### Kolom

```text
source_path
target_path
old_filename
new_filename
copy_status
rename_status
notes
```

## 4. 04_write_basic_metadata.py

### Tujuan

Menulis metadata dasar pada file hasil copy/rename.

### Aturan

Jika filename:

```text
ARTIS - JUDUL.mp3
```

Maka:

```text
Artist = ARTIS
Title = JUDUL
```

Jika tag sudah ada dan `overwrite_existing_tags=false`, jangan timpa.

### Output

```text
data/logs/metadata_write_report.csv
data/logs/metadata_write_report.xlsx
```

### Kolom

```text
file_path
old_title
new_title
old_artist
new_artist
old_album
new_album
old_genre
new_genre
status
notes
```

## 5. 05_sort_to_radio_folders.py

### Tujuan

Menyalin hasil bersih ke struktur `RADIO_AUDIO_LIBRARY`.

### Urutan Deteksi

1. Prefix nama file.
2. Keyword nama file.
3. Genre tag.
4. Folder asal.
5. Fallback.

### Fallback

Jika jelas sebagai musik:

```text
02_MUSIK_INDONESIA/Pop_Indonesia
```

Jika ragu:

```text
90_PERLU_DICEK
```

### Output

```text
data/logs/folder_sorting_report.csv
data/logs/folder_sorting_report.xlsx
```

## 6. 06_detect_possible_duplicates.py

### Tujuan

Mendeteksi kandidat duplikat tanpa menghapus.

### Kriteria

- nama sama,
- nama mirip,
- durasi mirip,
- ukuran mirip,
- artist/title sama.

### Output

```text
data/logs/possible_duplicates_report.csv
```

### Status

```text
DUPLIKAT_NAMA_SAMA
DUPLIKAT_DURASI_MIRIP
DUPLIKAT_TAG_SAMA
VERSI_BERBEDA_MUNGKIN
PERLU_DICEK_MANUAL
```

## 7. 07_validate_output_library.py

### Tujuan

Memvalidasi output akhir.

### Cek

- file bisa dibaca,
- path tidak terlalu panjang,
- tidak ada nama kosong,
- tidak ada forbidden character Windows,
- folder output sesuai struktur,
- file di ON_AIR_READY memenuhi syarat.

### Output

```text
data/logs/output_validation_report.csv
data/logs/output_validation_summary.md
```

## 8. 99_full_pipeline.py

### Tujuan

Menjalankan pipeline lengkap dengan flag.

Default:

```python
DRY_RUN = True
APPLY_RENAME = False
WRITE_METADATA = False
SORT_FILES = False
DETECT_DUPLICATES = True
```

### Mode

```bash
python scripts/99_full_pipeline.py --scan
python scripts/99_full_pipeline.py --preview
python scripts/99_full_pipeline.py --apply-rename
python scripts/99_full_pipeline.py --write-tags
python scripts/99_full_pipeline.py --sort
python scripts/99_full_pipeline.py --duplicates
python scripts/99_full_pipeline.py --validate
```

### Ringkasan Akhir

Buat:

```text
data/logs/final_summary.md
```

Isi:

```text
Total file ditemukan
Total file audio
Total berhasil scan
Total berhasil rename
Total metadata ditulis
Total masuk output
Total perlu dicek
Total duplikat diduga
Total audio bermasalah
Lokasi laporan
Lokasi output
```
