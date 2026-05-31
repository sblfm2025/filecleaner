# 08 — Duplikat dan Audio Bermasalah

## 1. Prinsip Utama

Sistem tidak boleh menghapus file duplikat otomatis.

Alasan: file yang terlihat duplikat bisa saja versi berbeda:

```text
Original
Radio Edit
Clean Version
Live
Acoustic
Remix
Instrumental
Karaoke
```

Untuk radio, versi `Clean Version` atau `Radio Edit` justru penting.

## 2. Deteksi Duplikat

Gunakan beberapa indikator:

### Nama sama

```text
Judika - Aku Yang Tersakiti.mp3
Judika - Aku Yang Tersakiti (1).mp3
```

### Nama mirip

Gunakan fuzzy matching seperti rapidfuzz.

### Durasi mirip

Misalnya selisih durasi kurang dari 2 detik.

### Ukuran file mirip

Ukuran hampir sama bisa menjadi indikasi.

### Tag sama

Artist dan Title sama.

## 3. Status Duplikat

Gunakan status:

```text
DUPLIKAT_NAMA_SAMA
DUPLIKAT_DURASI_MIRIP
DUPLIKAT_TAG_SAMA
VERSI_BERBEDA_MUNGKIN
PERLU_DICEK_MANUAL
```

## 4. Output Duplikat

Buat laporan:

```text
data/logs/possible_duplicates_report.csv
data/logs/possible_duplicates_report.xlsx
```

Kolom:

```text
group_id
file_path
filename
artist
title
duration_seconds
file_size_mb
similarity_score
duplicate_reason
recommended_action
```

## 5. Folder Duplikat Diduga

Copy kandidat duplikat ke:

```text
data/duplikat_diduga/
```

Namun jangan memindahkan dari output final secara destruktif.

## 6. Audio Bermasalah

File dianggap bermasalah jika:

- gagal dibaca,
- durasi 0,
- durasi terlalu pendek untuk lagu,
- metadata corrupt,
- file extension audio tetapi isi tidak valid,
- path terlalu panjang,
- permission denied,
- file sedang dipakai aplikasi lain,
- sample rate/bitrate tidak terbaca,
- ukuran 0 byte.

## 7. Durasi Anomali

Aturan awal:

```text
< 10 detik  : kemungkinan jingle/sfx atau file rusak
< 20 detik  : perlu cek jika diklaim lagu
> 15 menit  : kemungkinan program rekaman/talkshow
> 60 menit  : wajib masuk review kecuali memang rekaman program
```

## 8. Folder Audio Bermasalah

Masukkan/copy ke:

```text
data/audio_bermasalah/
```

atau output final:

```text
RADIO_AUDIO_LIBRARY/92_AUDIO_BERMASALAH/
```

## 9. Laporan Audio Bermasalah

Buat:

```text
data/logs/bad_audio_report.csv
```

Kolom:

```text
file_path
filename
extension
file_size_mb
duration_seconds
error_type
error_message
recommended_action
```

## 10. Recommended Action

Contoh:

```text
CEK_MANUAL
PUTAR_MANUAL
PERBAIKI_METADATA
GANTI_FILE_SUMBER
HAPUS_MANUAL_JIKA_YAKIN
MASUK_ARSIP_LAMA
```

Jangan buat action otomatis hapus.
