# Panduan Troubleshooting — RADIO_MUSIC_CLEANER

Dokumen ini berisi daftar masalah umum yang sering dihadapi saat memproses library audio dalam jumlah besar beserta solusi pemecahannya.

---

## Masalah 1: Error Batas Panjang Karakter Path Windows (Max Path 260)
* **Gejala**: Program menampilkan pesan error `FileNotFoundError` atau `PermissionError` saat menyalin file yang memiliki nama folder/file sangat panjang, meskipun file tersebut jelas ada.
* **Penyebab**: Windows secara default membatasi panjang alamat file (path) maksimal 260 karakter.
* **Solusi**: 
  1. **RADIO_MUSIC_CLEANER** sudah dilengkapi penanganan prefix path panjang Windows (`\\?\`). Namun, beberapa aplikasi pemutar musik radio (seperti RadioBoss lama) mungkin tetap tidak bisa memutar file dengan path terlalu panjang.
  2. Solusi terbaik adalah memperpendek nama folder root proyek Anda. Contohnya, jangan letakkan folder proyek di `C:\Users\NamaUser\Desktop\FolderKerja\RADIO_MUSIC_CLEANER\`, melainkan pindahkan ke `C:\RADIO_MUSIC_CLEANER\` atau `D:\RADIO_MUSIC_CLEANER\`.
  3. Perpendek nama file secara manual melalui Excel laporan preview sebelum dieksekusi.

---

## Masalah 2: File Audio Corrupt atau Rusak
* **Gejala**: Scanner menandai file dengan status `AUDIO_ERROR` atau metadata sama sekali tidak terbaca meskipun file bisa diputar.
* **Penyebab**: Kerusakan pada struktur header file audio (biasanya terjadi pada file hasil download YouTube Converter yang kurang sempurna atau kiriman WhatsApp).
* **Solusi**:
  1. File-file bermasalah ini akan otomatis diisolasi oleh tool ke folder `data/audio_bermasalah/` atau `92_AUDIO_BERMASALAH/` saat sortir.
  2. Buka software konverter audio gratis seperti **Audacity** atau **Format Factory**.
  3. Lakukan encode ulang file tersebut ke format MP3 standar (misalnya 192 kbps atau 320 kbps). Proses re-encode ini akan menulis ulang header file audio yang rusak sehingga menjadi normal dan terbaca oleh sistem.

---

## Masalah 3: Gagal Menginstal Dependency (pip install)
* **Gejala**: Muncul pesan error saat menjalankan perintah `pip install -r requirements.txt`, atau modul mutagen tidak ditemukan saat `run.py` dijalankan.
* **Penyebab**: Python tidak terdaftar di Windows Environment Path, atau koneksi internet terganggu.
* **Solusi**:
  1. Pastikan Anda mencentang pilihan **"Add Python to PATH"** saat menginstal Python di Windows. Jika belum, instal ulang Python Anda dan centang opsi tersebut.
  2. Jika instalasi offline diperlukan karena komputer radio tidak terhubung ke internet, unduh file `.whl` dependensi di komputer lain yang memiliki internet melalui situs [pypi.org](https://pypi.org/), lalu instal secara lokal menggunakan perintah:
     ```powershell
     pip install nama_file.whl
     ```

---

## Masalah 4: Karakter Nama File Rusak (Mojibake / Tanda Tanya)
* **Gejala**: Nama file hasil rename atau metadata lagu menampilkan karakter aneh seperti tanda tanya `?` atau simbol kotak-kotak.
* **Penyebab**: File asli menggunakan encoding non-UTF-8 (misalnya format penulisan karakter Tionghoa, Arab, atau Cyrillic lama).
* **Solusi**:
  1. Buka file tersebut di aplikasi **Mp3tag**.
  2. Tulis ulang nama Artist & Title menggunakan huruf latin standar.
  3. Simpan perubahan. Mp3tag secara otomatis akan mengubah encoding teks ke format UTF-16 yang kompatibel dengan Windows dan aplikasi siaran radio.
