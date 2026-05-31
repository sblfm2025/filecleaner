# 10 — Panduan Operator Windows

## 1. Tujuan

Panduan ini untuk operator radio yang ingin merapikan file lagu/audio tanpa merusak file asli.

## 2. Jangan Langsung Proses File Asli

Jangan buka folder sumber asli lalu langsung rename.

Cara aman:

```text
Copy sebagian file ke data/input_batch
Proses batch
Cek hasil
Baru lanjut batch berikutnya
```

## 3. Persiapan

Install tools gratis:

1. Python 3.x
2. VS Code atau Antigravity IDE
3. Mp3tag Windows
4. MusicBrainz Picard, opsional
5. ExifTool, opsional

## 4. Buka Project

Buka folder:

```text
RADIO_MUSIC_CLEANER
```

di VS Code atau Antigravity IDE.

## 5. Install Dependency

Buka terminal lalu jalankan:

```bash
pip install -r requirements.txt
```

## 6. Masukkan File Batch

Copy 20–50 file dulu untuk uji coba ke:

```text
data/input_batch/
```

Jangan langsung ratusan GB.

## 7. Jalankan Scan

```bash
python run.py --scan
```

Lihat laporan:

```text
data/logs/audio_scan_report.xlsx
```

## 8. Jalankan Preview Rename

```bash
python run.py --preview
```

Lihat:

```text
data/logs/filename_cleaning_preview.xlsx
```

Periksa apakah nama baru masuk akal.

## 9. Apply Rename

Jika preview aman:

```bash
python run.py --apply-rename
```

Sistem akan membuat salinan ke output, bukan mengubah file asli.

## 10. Tulis Metadata

```bash
python run.py --write-tags
```

Metadata hanya diisi jika kosong dan nama file jelas.

## 11. Sortir Folder

```bash
python run.py --sort
```

Hasil akhir ada di:

```text
data/output/RADIO_AUDIO_LIBRARY/
```

## 12. Cek Folder Perlu Dicek

File yang belum jelas masuk ke:

```text
90_PERLU_DICEK
```

Cek manual sebelum dipakai siaran.

## 13. Cek Duplikat

```bash
python run.py --duplicates
```

Jangan hapus otomatis. Lihat laporan dulu.

## 14. Validasi Output

```bash
python run.py --validate
```

Pastikan tidak ada file aneh di `ON_AIR_READY`.

## 15. Proses Batch Besar

Setelah uji 20–50 file berhasil, lanjut:

```text
5 GB
10 GB
30–50 GB
```

Untuk ratusan GB, proses bertahap.

## 16. Setelah Batch Selesai

1. Cek output.
2. Pindahkan hasil final ke storage library radio.
3. Kosongkan input_batch secara manual jika sudah aman.
4. Simpan log batch.
5. Lanjut batch berikutnya.

## 17. Jangan Lakukan Ini

```text
Jangan proses file asli satu-satunya.
Jangan hapus file duplikat tanpa cek.
Jangan masukkan PERLU_DICEK ke RadioBoss.
Jangan proses file yang sedang dipakai RadioBoss siaran.
Jangan percaya 100% metadata otomatis.
```

## 18. Kapan Pakai Mp3tag

Gunakan Mp3tag untuk finishing:

- isi genre massal,
- cek Artist/Title,
- edit tag yang masih kosong,
- export ulang jika perlu.

## 19. Kapan Pakai MusicBrainz Picard

Gunakan Picard hanya untuk lagu resmi yang sulit dikenali.

Jangan pakai Picard untuk:

- jingle,
- iklan,
- ILM,
- rekaman talkshow,
- audio lokal non-komersial.
