# 02 — Struktur Project

Developer harus membuat folder project sebagai berikut:

```text
RADIO_MUSIC_CLEANER/
├── README.md
├── requirements.txt
├── run.py
├── config/
│   ├── cleaner_rules.json
│   ├── folder_mapping.json
│   ├── metadata_defaults.json
│   └── batch_settings.json
├── scripts/
│   ├── 01_scan_audio_library.py
│   ├── 02_clean_filename_preview.py
│   ├── 03_apply_filename_cleaning.py
│   ├── 04_write_basic_metadata.py
│   ├── 05_sort_to_radio_folders.py
│   ├── 06_detect_possible_duplicates.py
│   ├── 07_validate_output_library.py
│   └── 99_full_pipeline.py
├── src/
│   ├── __init__.py
│   ├── audio_reader.py
│   ├── filename_cleaner.py
│   ├── metadata_writer.py
│   ├── folder_sorter.py
│   ├── duplicate_detector.py
│   ├── batch_manager.py
│   ├── report_writer.py
│   ├── safe_file_ops.py
│   └── utils.py
├── data/
│   ├── input/
│   ├── input_batch/
│   ├── output/
│   ├── output_batch/
│   ├── perlu_dicek/
│   ├── duplikat_diduga/
│   ├── audio_bermasalah/
│   ├── original_backup/
│   └── logs/
└── docs/
    ├── PANDUAN_OPERATOR.md
    ├── PANDUAN_STRUKTUR_LIBRARY_RADIO.md
    ├── PANDUAN_MP3TAG.md
    ├── PANDUAN_MUSICBRAINZ_PICARD.md
    └── TROUBLESHOOTING.md
```

## 1. README.md

Berisi:

- fungsi tool,
- cara install Python,
- cara install dependency,
- cara memasukkan file audio,
- cara menjalankan scan,
- cara menjalankan preview,
- cara apply rename,
- cara tulis metadata,
- cara sortir folder,
- peringatan keamanan.

## 2. requirements.txt

Minimal:

```text
mutagen
pandas
openpyxl
rapidfuzz
```

`rapidfuzz` opsional tetapi disarankan untuk deteksi nama mirip.

## 3. run.py

File entry point sederhana agar operator tidak perlu mengingat banyak script.

Contoh penggunaan:

```bash
python run.py --scan
python run.py --preview
python run.py --apply-rename
python run.py --write-tags
python run.py --sort
python run.py --duplicates
python run.py --summary
```

## 4. Folder config

Berisi file konfigurasi yang bisa diedit tanpa menyentuh kode.

### cleaner_rules.json

Untuk daftar kata kotor, karakter pengganti, aturan bracket, dan kata yang harus dipertahankan.

### folder_mapping.json

Untuk mapping keyword/prefix ke folder output radio.

### metadata_defaults.json

Untuk album default, genre default, comment default.

### batch_settings.json

Untuk pengaturan batch seperti ukuran maksimal batch, lokasi input/output, dan mode aman.

## 5. Folder scripts

Berisi script mandiri yang bisa dijalankan satu per satu.

Setiap script wajib:

- punya `if __name__ == "__main__":`,
- bisa dijalankan dari root project,
- menulis log,
- tidak crash total jika satu file error.

## 6. Folder src

Berisi modul reusable agar script tidak penuh kode duplikat.

### audio_reader.py

Fungsi:

- deteksi file audio,
- baca metadata,
- baca durasi,
- baca bitrate/sample rate jika tersedia.

### filename_cleaner.py

Fungsi:

- bersihkan nama file,
- deteksi pola `Artis - Judul`,
- kapitalisasi aman,
- validasi nama file Windows.

### metadata_writer.py

Fungsi:

- tulis metadata dasar,
- jangan overwrite tag bagus,
- dukung MP3 ID3,
- handling format lain.

### folder_sorter.py

Fungsi:

- tentukan folder tujuan,
- cek prefix,
- cek keyword,
- cek genre,
- fallback ke `90_PERLU_DICEK`.

### duplicate_detector.py

Fungsi:

- deteksi nama mirip,
- durasi mirip,
- ukuran mirip,
- artist/title sama.

### batch_manager.py

Fungsi:

- membuat batch,
- melacak status batch,
- resume jika terhenti,
- skip file yang sudah diproses.

### report_writer.py

Fungsi:

- tulis CSV,
- tulis XLSX,
- tulis Markdown summary,
- append log bertahap.

### safe_file_ops.py

Fungsi:

- copy aman,
- hindari overwrite,
- buat nama unik,
- validasi path,
- tangani path panjang Windows.

## 7. Folder data

Folder data adalah area kerja. Operator hanya boleh memasukkan salinan file ke sini, bukan file asli satu-satunya.

### input

Untuk uji coba kecil atau input umum.

### input_batch

Untuk batch aktif.

### output

Untuk hasil akhir.

### output_batch

Untuk hasil sementara tiap batch.

### perlu_dicek

Untuk file ambigu.

### duplikat_diduga

Untuk file yang dicurigai duplikat.

### audio_bermasalah

Untuk file corrupt, gagal dibaca, durasi aneh, atau error metadata.

### original_backup

Opsional untuk salinan backup.

### logs

Semua laporan proses.

## 8. Folder docs

Berisi panduan operator dan troubleshooting dalam bahasa Indonesia.

Developer wajib membuat dokumentasi yang tidak terlalu teknis agar operator radio bisa menjalankan tool tanpa bingung.
