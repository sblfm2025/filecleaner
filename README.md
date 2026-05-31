# 📻 Radio Audio Library Manager (Filecleaner v4.0)

Aplikasi stasiun radio profesional berbasis Command Line Interface (CLI) Windows, REST API Backend Lokal, dan Web UI Dashboard Premium. Sistem ini dirancang untuk memindai, mengklasifikasi, menyortir, melakukan *fingerprint* suara, meninjau usulan metadata secara visual, dan mengekspor playlist siaran secara otomatis, terstruktur, dan aman tanpa menggandakan berkas fisik.

Aplikasi ini menggabungkan konsep terbaik dari tiga dunia: **sidik jari audio AcoustID & MusicBrainz** (terinspirasi Picard), ** visual review & batch tag editor** (terinspirasi music-tag-web), dan **keamanan operasi berkas lokal serta dry-run** (fondasi filecleaner).

---

## 🌟 Prinsip Desain Utama

1. **Rule-Based Classifier Sebagai Pagar Utama**: Menentukan media tipe dan folder tujuan dengan signals terstruktur. Sidik jari suara AcoustID hanya dijalankan pada berkas musik resmi yang ambigu.
2. **AcoustID & MusicBrainz Hanya Untuk Lagu Resmi**: Aset radio non-musik seperti *Jingle, Iklan, Bumper, ILM (PSA), Bed, dan Program* disaring ketat di awal dan **tidak akan dikirim ke API luar** guna menghemat bandwidth dan kuota API.
3. **Metadata Tidak Overwrite Otomatis**: Hasil usulan metadata dikelompokkan menjadi mode: `AUTO_WRITE_EMPTY_TAGS` (jika tag kosong & skor AcoustID >= 0.90), `SUGGEST_ONLY` (sebagai usulan opsional), atau `REVIEW_CONFLICT` (jika terjadi konflik tag asli vs usulan).
4. **Visual Review Queue & Dashboard**: Segala berkas yang diragukan atau berkonflik disajikan dalam antrean visual di browser operator sebelum diterapkan fisik di disk.
5. **Master Folder Minim Duplikasi**: File fisik disimpan di satu lokasi master tunggal. Kategori genre, suasana hati (mood), dekade, artis, maupun rotasi siaran direpresentasikan sebagai pointer daftar putar logis (**Playlist M3U**), bukan menyalin file secara fisik.
6. **Log Operasi & Pemulihan (Rollback) Keselamatan**: Setiap modifikasi fisik dicatat ke audit log transparan. Fitur rollback dilengkapi **Pagar Pengaman** ketat yang menjamin file di folder input asli Anda tidak akan pernah diubah atau disentuh.

---

## 🔄 Alur Kerja Sistem v4.0

```text
Scan Input Directory
  ├── Clean Filename Preview
  └── Rule-Based Multi-Stage Classification
        ├── AUTO_SORT (Skor >= 85) ───► Siap Pindah Fisik ke Master Library
        ├── NEEDS_REVIEW (Skor < 60) ──► Dialokasikan ke Subfolder 90_NEEDS_REVIEW/
        └── Musik Resmi Ambigu ────────► AcoustID Fingerprint Lookup (fpcalc)
                                              └── MusicBrainz REST API Lookup
                                                    └── Metadata Suggestion Engine
                                                          └── Web UI Review Queue Draft
                                                                └── Operator Approve/Edit/Reject
                                                                      ├── Apply Approved Changes
                                                                      ├── Audit Log & Rollback Manifest
                                                                      ├── Build Index Catalog Database
                                                                      └── Export Playlist RadioBoss (M3U)
```

---

## 📂 Struktur Folder Master Library

Sistem menyusun berkas ke dalam direktori master yang rapi dan terorganisir di bawah `RADIO_AUDIO_MASTER_LIBRARY/`:

```text
RADIO_AUDIO_MASTER_LIBRARY/
├── 01_MASTER_MUSIC/                    # Kategori Musik Nasional/Utama
│   └── 10_UNKNOWN_RELEASE_TYPE/        # Fallback musik umum v4.0
├── 02_MASTER_LOCAL_REGIONAL/           # Musik daerah (Bugis, Makassar, Toraja, Mandar, dll)
├── 03_MASTER_RELIGIOUS/                # Lagu Islami, Sholawat, & Murottal Quran
├── 04_MASTER_INTERNATIONAL/            # Musik Barat & K-Pop
├── 05_MASTER_INSTRUMENTAL_BED/         # Musik latar belakang siaran / Newsbed
├── 06_MASTER_RADIO_ASSETS/             # Aset internal radio (Jingle, Bumper, Stinger)
├── 07_MASTER_COMMERCIAL_PUBLIC_SERVICE/# Iklan komersial & Iklan Layanan Masyarakat (ILM/PSA)
├── 08_MASTER_PROGRAM_RECORDINGS/       # Rekaman talkshow & podcast penyiaran
├── 09_MASTER_SPECIAL_EVENT/            # Rekaman siaran luar & acara khusus
├── 20_INDEX_CATALOG/                   # Katalog playlist logis M3U per artis/genre/mood/dekade
├── 30_PLAYLIST_EXPORT/                 # Ekspor M3U final untuk software siaran RadioBoss
├── 90_NEEDS_REVIEW/                    # Folder tinjauan fisik per jenis konflik
│   ├── 01_UNKNOWN_ARTIST_TITLE/
│   ├── 02_LOW_CONFIDENCE_CATEGORY/
│   ├── 03_CONFLICTING_SIGNALS/
│   ├── 11_FINGERPRINT_NO_MATCH/
│   ├── 13_FINGERPRINT_LOW_CONFIDENCE/
│   └── 14_MUSICBRAINZ_METADATA_CONFLICT/
├── 91_DUPLICATE_SUSPECTED/             # Berkas tersangka duplikat yang disendirikan
└── 92_BAD_AUDIO/                       # Berkas audio corrupt atau rusak
```

---

## ⚙️ Persyaratan Sistem & Instalasi

### Persyaratan:
* Sistem Operasi Windows 10/11
* Python 3.8 atau yang lebih baru
* Koneksi internet (opsional, hanya untuk fingerprint lookup ke web service AcoustID)
* Program **`fpcalc.exe`** portable (dapat diletakkan di dalam folder `bin/` proyek atau ditambahkan ke Environment PATH Windows Anda).

### Cara Instalasi:
1. Pastikan Python terinstal di PC Anda (centang **Add Python to PATH** saat instalasi).
2. Unduh atau salin proyek ini ke PC lokal Anda.
3. Buka terminal PowerShell atau Command Prompt di folder proyek ini, lalu jalankan instalasi dependensi:
   ```powershell
   pip install -r requirements.txt
   ```

---

## 💻 Panduan Pengoperasian Menu CLI v4.0

Jalankan perintah entri utama tanpa argumen untuk masuk ke **Menu Utama CLI Interaktif** dalam Bahasa Indonesia:
```powershell
python run.py
```

### Opsi Menu yang Tersedia:
1. **Ubah Folder Input Lagu**: Mengubah direktori input lagu stasiun radio (drag-drop folder didukung).
2. **Pindai Folder Musik & Baca Metadata (Scan)**: Memindai berkas audio di disk.
3. **Lihat Simulasi Pembersihan Nama Berkas (Preview)**: Dry-run preview nama berkas bersih.
4. **Jalankan Audit Mode Aman**: Scan + Preview + Duplikat + QA (dry-run penuh).
5. **Salin & Bersihkan Nama File**: Menyalin dan merapikan fisik file ke folder batch.
6. **Tulis Tag Metadata Dasar**: Mengisi tag Artist & Title dasar pada file.
7. **Susun File ke Folder Kategori**: Memindahkan file ke folder master sesuai klasifikasi.
8. **Deteksi & Kumpulkan Berkas Duplikat**: Mengidentifikasi duplikat audio.
9. **Audit Validasi Kualitas Library Akhir**: Validasi QA berkas keluaran.
10. **AcoustID Fingerprint Kandidat Lagu Resmi**: Mengekstraksi sidik jari audio suara.
11. **Evaluasi Usulan Metadata AcoustID + MusicBrainz**: Kueri detail album/tahun & evaluasi konflik tag.
12. **Susun Draf Antrean Tinjauan Operator**: Merangkum usulan ke database review queue draft.
13. **Eksekusi Persetujuan Perubahan Fisik**: Menerapkan approved/edited berkas ke disk.
14. **Bangun Katalog Master & Playlists M3U**: Kataloger master dinamis.
15. **Ekspor Daftar Putar Siaran RadioBoss**: Pengekspor playlist final RadioBoss.
16. **Audit Klasifikasi Standalone**: Menjalankan pengujian klasifikasi instan.
17. **Panduan Finishing**: Petunjuk penggunaan Mp3tag & MusicBrainz Picard.
18. **Keluar**.

---

## 🛠️ Flag Perintah CLI Standalone

Anda juga dapat memanggil tugas tertentu secara langsung melalui parameter baris perintah (cocok untuk otomasi penjadwalan task):

* **Menjalankan Seluruh Alur Analisis Mode Aman (Dry-run v4.0 lengkap)**:
  ```powershell
  python run.py --all-safe
  ```
* **Audit Klasifikasi Instan Tanpa Mengubah Berkas Fisik**:
  ```powershell
  python run.py --classify --input-dir "D:\FolderLaguRadio"
  ```
* **Fingerprint AcoustID Massal**:
  ```powershell
  python run.py --fingerprint-candidates
  ```
* **Mengevaluasi Usulan Metadata**:
  ```powershell
  python run.py --metadata-suggestions
  ```
* **Menyusun Antrean Review Queue**:
  ```powershell
  python run.py --build-review-queue
  ```
* **Menerapkan Modifikasi Fisik yang Disetujui Operator**:
  ```powershell
  python run.py --apply-approved
  ```
* **Mengekspor Playlist Pointer Logis M3U untuk RadioBoss**:
  ```powershell
  python run.py --export-playlists
  ```

---

## 🖥️ Portal Web Review Editor & Dashboard Interaktif (localhost:8000)

Untuk memberikan pengalaman visual premium seperti `music-tag-web`, aplikasi dilengkapi dengan server API Backend dan Web UI Dashboard interaktif.

### Cara Menjalankan Server Backend API:
Jalankan perintah ini di terminal Windows Anda:
```powershell
python -c "from src.web_review_api import start_api_server; start_api_server()"
```
Server akan menyala di alamat **`http://localhost:8000`**.

### Fitur Visual Dashboard (`dashboard.html`):
1. **Tabel Antrean Tinjauan (Review Queue Editor)**: Tinjau usulan metadata (Artist, Title, Album, Year, Genre) vs tag asli di disk.
2. **Tindakan Interaktif**: Klik **Approve** untuk menyetujui usulan, **Reject** untuk membuang berkas ke folder bad audio/duplikat, atau klik **Edit** untuk memodifikasi tag secara langsung di tabel.
3. **Bulk Action**: Setujui ratusan lagu ber-confidence tinggi secara massal dalam satu klik.
4. **Log & Rollback Keselamatan**: Klik menu audit log untuk memantau detail aktivitas fisik file. Klik **Rollback** pada entri log untuk memulihkan berkas tersebut ke nama dan tag ID3 asalnya secara instan.
5. **Offline Mode File-Fallback**: Jika API server tidak aktif, Anda cukup drag-and-drop berkas `classification_report.csv` atau `folder_sorting_report.csv` langsung ke browser untuk memvisualisasikan data grafik interaktif Chart.js.

---

## 🧪 Verifikasi QA & Unit Test Terpadu

Pengembangan ini ditunjang dengan rangkaian pengujian unit test wajib untuk memastikan stabilitas sistem 100% lulus QA.

* **Menjalankan Seluruh Unit Test Terpadu**:
  ```powershell
  python test_manager.py
  ```
  *(Menguji kelayakan AcoustID, evaluator suggestion engine, review queue builder draft, pencatatan log CSV transparan, pemulihan rollback, serta verifikasi kepatuhan pagar pengaman).*

* **Menjalankan Unit Test Skenario Klasifikasi (20 Kasus Uji)**:
  ```powershell
  python test_classifier.py
  ```
  *(Menguji saringan jingle/iklan, dialek Bugis dengan sinyal ganda/tunggal, sholawat religi, murottal Quran, WhatsApp audio, nama file berbahaya love/background, penyimpangan durasi, dan fallback musik unknown).*

---

## ⚠️ Kebijakan Lisensi & Pagar Pengaman Keselamatan

> [!IMPORTANT]
> 1. **FILE INPUT ASLI DIJAMIN AMAN**: Sistem v4.0 ini menerapkan prinsip *safe file operation*. Berkas musik stasiun radio asli Anda di folder input hanya dibaca (*read-only*) dan disalin secara aman. Sistem tidak akan pernah mengubah, mengganti nama, atau menghapus file asli Anda.
> 2. **NO AUTO-OVERWRITE**: Sistem tidak akan menimpa tag ID3 file audio secara otomatis tanpa persetujuan operator visual di dashboard atau konfigurasi eksplisit dari user.
> 3. **PAGAR PENGAMAN ROLLBACK**: Fitur Rollback membatasi diri hanya untuk memodifikasi berkas hasil pemrosesan di folder output master. Sistem secara cerdas akan menolak keras memproses pemulihan jika path berkas mengarah ke folder input stasiun radio asli guna mencegah kerusakan data primer stasiun radio.
> 4. **TIDAK MENGHAPUS BERKAS FISIK**: Berkas duplikat dan corrupt tidak dihapus secara otomatis dari disk, melainkan dipisahkan secara aman ke folder `91_DUPLICATE_SUSPECTED/` dan `92_BAD_AUDIO/` agar operator stasiun radio dapat meninjaunya kembali dengan tenang.

---
*RADIO AUDIO LIBRARY MANAGER v4.0 dikembangkan secara cermat untuk stasiun radio modern yang menghargai ketertiban data, efisiensi bandwidth siaran, serta keselamatan aset digital.*
