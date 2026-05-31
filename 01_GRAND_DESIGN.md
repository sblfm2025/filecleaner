# 01 — Grand Design RADIO_MUSIC_CLEANER

## 1. Nama Sistem

```text
RADIO_MUSIC_CLEANER
```

## 2. Latar Belakang

Radio publik lokal biasanya memiliki ribuan file audio dari berbagai sumber:

- lagu Indonesia,
- lagu daerah,
- lagu religi,
- lagu internasional,
- jingle,
- bumper,
- iklan,
- ILM,
- rekaman talkshow,
- rekaman WhatsApp,
- file lama,
- file duplikat,
- file dengan metadata kosong,
- file dengan nama kotor seperti `Official Video`, `Lyrics`, `320kbps`, `Download Lagu`, dan sebagainya.

Jika file langsung dipakai di RadioBoss atau sistem playlist tanpa dirapikan, maka penyiar akan kesulitan mencari lagu, metadata tampil kotor, playlist sulit diaudit, dan file bermasalah bisa masuk siaran.

## 3. Tujuan Utama

Bangun tool lokal Windows yang dapat:

1. Memindai folder audio besar.
2. Membuat laporan isi library.
3. Membersihkan nama file secara aman.
4. Mengisi metadata dasar dari pola nama file.
5. Menyortir audio ke struktur folder radio lokal.
6. Mendeteksi kemungkinan duplikat.
7. Memisahkan file ambigu dan bermasalah.
8. Memproses ratusan GB secara batch.
9. Menjaga file asli tetap aman.
10. Membuat laporan yang bisa diaudit.

## 4. Prinsip Keamanan

Sistem harus sangat konservatif.

```text
File asli tidak boleh diubah.
File asli tidak boleh dihapus.
File asli tidak boleh di-rename.
Semua proses final dilakukan pada salinan/output.
Default sistem adalah preview/dry-run.
Jika ragu, masukkan ke PERLU_DICEK.
```

## 5. Bentuk Sistem

Tahap awal jangan membuat aplikasi GUI besar. Buat tool lokal berbasis Python script + CLI sederhana.

Alasan:

- lebih ringan,
- mudah diaudit,
- cocok untuk ratusan GB,
- tidak perlu server,
- tidak butuh database online,
- mudah diperbaiki di Antigravity/VS Code.

Setelah script stabil, baru boleh dikembangkan ke GUI sederhana.

## 6. Target Platform

```text
OS utama      : Windows 10/11
IDE           : Antigravity IDE / VS Code
Runtime       : Python 3.x
Eksekusi      : PowerShell, CMD, atau terminal IDE
Output laporan: CSV dan XLSX
```

## 7. Tools Gratis

Gunakan:

```text
Python
mutagen
pandas
openpyxl
rapidfuzz, opsional untuk fuzzy duplicate
Mp3tag Windows, untuk finishing metadata manual
MusicBrainz Picard, untuk file musik resmi yang sulit dikenali
ExifTool, opsional untuk inspeksi metadata teknis
```

Dilarang:

```text
API berbayar
Spotify scraping
Shazam API
layanan fingerprint berbayar
database online wajib login
fitur yang mengharuskan koneksi internet
```

## 8. Sasaran Hasil Akhir

Setelah proses selesai, sistem menghasilkan:

```text
data/output/RADIO_AUDIO_LIBRARY/
```

Berisi audio yang sudah dikelompokkan untuk kebutuhan radio publik lokal.

Sistem juga menghasilkan:

```text
data/logs/audio_scan_report.xlsx
data/logs/filename_cleaning_preview.xlsx
data/logs/metadata_write_report.xlsx
data/logs/folder_sorting_report.xlsx
data/logs/possible_duplicates_report.xlsx
data/logs/final_summary.md
```

## 9. Batasan Sistem

Sistem tidak harus mengenali semua lagu secara otomatis.

Sistem tidak boleh mengarang judul/artis.

Sistem tidak boleh menebak terlalu agresif.

Sistem hanya boleh mengisi metadata jika pola cukup jelas, misalnya:

```text
ARTIS - JUDUL.mp3
```

Jika file bernama:

```text
Track 01.mp3
Audio WhatsApp 2025.mp3
Lagu Viral.mp3
Unknown.mp3
```

maka masukkan ke:

```text
90_PERLU_DICEK
```

## 10. Filosofi Kualitas

Untuk radio, metadata salah lebih berbahaya daripada metadata kosong.

Sistem harus mengutamakan:

```text
aman
terukur
bisa diaudit
tidak merusak file asli
ramah operator
mudah dikembangkan
```
