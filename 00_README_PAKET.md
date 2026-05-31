# RADIO MUSIC CLEANER — Paket Arahan Teknis Developer

Paket ini berisi arahan teknis terstruktur untuk membangun tool lokal Windows bernama **RADIO_MUSIC_CLEANER**.

Tujuan utama tool ini adalah membantu radio publik lokal merapikan ratusan GB file audio/lagu yang berantakan dengan cara aman:

- file asli tidak diubah,
- proses dilakukan per batch,
- ada mode preview/dry-run,
- nama file dibersihkan,
- metadata dasar diperbaiki,
- file disortir ke struktur folder radio,
- file ambigu dipisahkan ke `PERLU_DICEK`,
- laporan CSV/XLSX dibuat untuk audit.

## Isi Dokumen

1. `01_GRAND_DESIGN.md`  
   Gambaran besar sistem, tujuan, batasan, dan prinsip keamanan.

2. `02_STRUKTUR_PROJECT.md`  
   Struktur folder project yang harus dibuat oleh developer.

3. `03_STRUKTUR_LIBRARY_RADIO.md`  
   Struktur folder hasil akhir untuk kebutuhan radio publik lokal.

4. `04_BATCH_PROCESSING_RATUSAN_GB.md`  
   Desain teknis agar aman memproses data ratusan GB sampai 1 TB.

5. `05_KONFIGURASI_JSON.md`  
   Spesifikasi file konfigurasi: aturan rename, mapping folder, metadata default.

6. `06_SPESIFIKASI_SCRIPT_PYTHON.md`  
   Rincian script Python yang harus dibuat.

7. `07_METADATA_AUDIO.md`  
   Aturan metadata audio, tag MP3, penanganan file non-lagu, dan prinsip aman.

8. `08_DUPLIKAT_AUDIO_BERMASALAH.md`  
   Deteksi duplikat, file rusak, audio bermasalah, dan aturan tidak hapus otomatis.

9. `09_CLI_DAN_MODE_AMAN.md`  
   Desain perintah CLI, dry-run, apply, resume, dan eksekusi batch.

10. `10_PANDUAN_OPERATOR_WINDOWS.md`  
    Panduan operator non-teknis untuk menjalankan tool di Windows.

11. `11_INTEGRASI_MP3TAG_PICARD.md`  
    Panduan memakai Mp3tag dan MusicBrainz Picard sebagai finishing manual gratis.

12. `12_TESTING_QA_CHECKLIST.md`  
    Checklist pengujian agar sistem aman sebelum dipakai ke file besar.

13. `13_PROMPT_MASTER_ANTIGRAVITY_GEMINI.md`  
    Prompt utama siap tempel ke Antigravity IDE/Gemini.

14. `XX_FIREBASE.MD`  
    Konfigurasi Firebase 
    

## Prinsip Utama

Developer wajib mengikuti prinsip ini:

```text
JANGAN UBAH FILE ASLI.
JANGAN HAPUS FILE OTOMATIS.
JANGAN OVERWRITE FILE TANPA PROTEKSI.
DEFAULT HARUS DRY-RUN/PREVIEW.
FILE RAGU MASUK PERLU_DICEK.
METADATA SALAH LEBIH BERBAHAYA DARIPADA METADATA KOSONG.
```

## Target Penggunaan

Tool ini ditujukan untuk PC Windows dan dapat dibuka di:

- Antigravity IDE,
- VS Code,
- terminal PowerShell/CMD.

Semua tools harus 100% gratis:

- Python,
- library Python gratis,
- Mp3tag Windows,
- MusicBrainz Picard,
- ExifTool opsional.

Tidak boleh menggunakan API berbayar, scraping Spotify, Shazam API, atau sistem login online.
