# 13 — Prompt Master untuk Antigravity IDE / Gemini

Salin prompt ini ke Antigravity IDE/Gemini.

---

Saya ingin Anda membangun project lokal Windows bernama **RADIO_MUSIC_CLEANER**.

Tujuan project ini adalah membantu merapikan ratusan GB file audio/lagu radio lokal yang berantakan. Sistem harus 100% gratis, berjalan lokal di PC, tidak membutuhkan server, login, API berbayar, Spotify scraping, Shazam API, atau layanan online wajib.

## Prinsip Wajib

1. Jangan ubah file asli.
2. Jangan hapus file otomatis.
3. Jangan overwrite file output.
4. Default harus dry-run/preview.
5. Semua proses apply harus bekerja pada salinan file.
6. File ambigu masuk `PERLU_DICEK`.
7. Metadata salah lebih berbahaya daripada metadata kosong.
8. Sistem harus aman untuk batch ratusan GB dengan proses per batch.
9. Jangan load semua file ke RAM sekaligus.
10. Harus ada laporan CSV/XLSX dan summary Markdown.

## Stack

Gunakan:

- Python 3.x
- mutagen
- pandas
- openpyxl
- rapidfuzz jika perlu untuk deteksi duplikat

Buat `requirements.txt`.

## Struktur Project

Buat struktur:

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

## Struktur Output Radio

Hasil akhir harus menggunakan struktur:

```text
RADIO_AUDIO_LIBRARY/
├── 00_ON_AIR_READY/
│   ├── Musik_Indonesia/
│   ├── Musik_Lokal_Daerah/
│   ├── Musik_Religi/
│   ├── Musik_Internasional/
│   ├── Jingle/
│   ├── Bumper/
│   ├── Iklan_Aktif/
│   └── ILM_Insert/
├── 01_MUSIK_LOKAL_DAERAH/
│   ├── Bugis/
│   ├── Makassar/
│   ├── Mandar/
│   ├── Toraja/
│   └── Artis_Lokal_Pinrang/
├── 02_MUSIK_INDONESIA/
│   ├── Pop_Indonesia/
│   ├── Dangdut/
│   ├── Religi/
│   ├── Nostalgia/
│   └── Lagu_Anak_Remaja/
├── 03_MUSIK_INTERNASIONAL/
│   ├── Western_Pop/
│   ├── Classic_Hits/
│   ├── KPop/
│   └── Soundtrack/
├── 04_NON_MUSIK_SIARAN/
│   ├── Jingle_Station_ID/
│   ├── Bumper_Program/
│   ├── Iklan/
│   ├── ILM_Layanan_Publik/
│   ├── Newsbed_Talkshow/
│   └── Event_Khusus/
├── 05_PROGRAM_REKAMAN/
│   ├── Talkshow/
│   ├── Wawancara/
│   ├── Berita_Lokal/
│   ├── Podcast/
│   └── Event_Off_Air/
├── 06_ROTASI_PLAYLIST/
│   ├── Pagi/
│   ├── Siang/
│   ├── Sore/
│   ├── Malam/
│   ├── Weekend/
│   ├── Lagu_Baru/
│   ├── Lagu_Lokal_Prioritas/
│   └── Emergency_Playlist/
├── 90_PERLU_DICEK/
├── 91_DUPLIKAT_DIDUGA/
├── 92_AUDIO_BERMASALAH/
└── 99_ARSIP_LAMA/
```

## Script yang Harus Dibuat

### 01_scan_audio_library.py

Scan semua file audio, baca metadata, durasi, ukuran, path, dan status. Output CSV/XLSX.

### 02_clean_filename_preview.py

Buat preview nama file baru tanpa mengubah file.

### 03_apply_filename_cleaning.py

Copy file dari input ke output, rename salinan, jangan ubah sumber asli.

### 04_write_basic_metadata.py

Isi metadata dasar dari pola `Artis - Judul` jika tag kosong. Jangan overwrite tag bagus.

### 05_sort_to_radio_folders.py

Sortir ke struktur folder radio berdasarkan prefix, keyword, genre, dan fallback.

### 06_detect_possible_duplicates.py

Deteksi duplikat berdasarkan nama mirip, durasi mirip, ukuran mirip, dan tag sama. Jangan hapus.

### 07_validate_output_library.py

Validasi output, path, folder, file error, dan kelayakan ON_AIR_READY.

### 99_full_pipeline.py

Jalankan pipeline dengan flag aman.

## CLI

Buat `run.py` dengan perintah:

```bash
python run.py --scan
python run.py --preview
python run.py --all-safe
python run.py --apply-rename
python run.py --write-tags
python run.py --sort
python run.py --duplicates
python run.py --validate
python run.py --resume
```

Default tidak boleh mengubah file.

Apply mode harus minta konfirmasi `YES`.

## Batch Processing

Tambahkan:

- batch_id,
- process_manifest.csv,
- status per file,
- resume,
- skip completed,
- CSV append,
- tidak load semua file ke RAM.

Status file:

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

## Metadata

Untuk lagu:

```text
Artist = bagian sebelum tanda -
Title  = bagian setelah tanda -
Album  = Radio SBL Library jika kosong
Genre  = sesuai kategori jika kosong
Comment = Processed by RADIO_MUSIC_CLEANER jika kosong
```

Jangan menulis metadata otomatis untuk file ambigu seperti:

```text
Track 01.mp3
Audio WhatsApp.mp3
Unknown.mp3
Lagu Viral.mp3
New Recording.mp3
```

## Dokumentasi

Buat dokumentasi bahasa Indonesia:

- README.md
- PANDUAN_OPERATOR.md
- PANDUAN_STRUKTUR_LIBRARY_RADIO.md
- PANDUAN_MP3TAG.md
- PANDUAN_MUSICBRAINZ_PICARD.md
- TROUBLESHOOTING.md

## Kriteria Berhasil

Project dianggap berhasil jika:

1. Bisa scan folder audio.
2. Bisa membuat laporan CSV/XLSX.
3. Bisa preview rename.
4. Bisa copy dan rename salinan.
5. Bisa isi metadata dasar tanpa overwrite tag bagus.
6. Bisa sortir ke struktur radio.
7. Bisa deteksi duplikat tanpa hapus.
8. Bisa memproses batch besar tanpa load semua file ke RAM.
9. Bisa resume setelah proses terhenti.
10. File asli tetap aman.

Kerjakan bertahap, mulai dari fondasi aman, lalu preview, lalu apply, metadata, sorting, duplikat, validasi, dan dokumentasi.
