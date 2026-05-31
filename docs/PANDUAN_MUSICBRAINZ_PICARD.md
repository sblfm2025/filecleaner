# Panduan Finishing Menggunakan MusicBrainz Picard

**MusicBrainz Picard** adalah aplikasi open-source gratis yang dikembangkan oleh yayasan nirlaba MetaBrainz. Picard sangat ampuh untuk melengkapi tag metadata lagu resmi (nasional maupun internasional) yang sulit dikenali secara manual karena ia menggunakan teknologi **Audio Fingerprint (AcoustID)** untuk mengenali lagu dari frekuensi suaranya, bukan hanya berdasarkan nama file.

---

## Langkah 1: Instalasi MusicBrainz Picard
1. Unduh aplikasi di situs resmi: [picard.musicbrainz.org](https://picard.musicbrainz.org/download/).
2. Pasang aplikasi tersebut pada PC Windows Anda.

---

## Langkah 2: Mengimpor File Lagu
1. Buka MusicBrainz Picard.
2. Klik tombol **Add Folder** di bilah menu atas.
3. Pilih folder yang ingin Anda lengkapi tag-nya, misalnya folder Pop Indonesia:
   ```text
   data/output/RADIO_AUDIO_LIBRARY/02_MUSIK_INDONESIA/Pop_Indonesia/
   ```
4. File lagu akan masuk ke kolom sebelah kiri bernama **Unmatched Files** (File belum dicocokkan).

---

## Langkah 3: Pencarian Berdasarkan Nama Berkas (Lookup)
1. Pilih file lagu di kolom kiri (bisa blok semuanya menggunakan `Ctrl + A`).
2. Klik tombol **Lookup** di menu atas.
3. Picard akan mencari kecocokan nama berkas di database musik MusicBrainz.
4. Jika lagu ditemukan, ia akan pindah ke kolom sebelah kanan dan dikelompokkan ke dalam folder Album resminya dengan ikon berwarna hijau atau kuning.

---

## Langkah 4: Pencarian Berdasarkan Frekuensi Suara (Scan AcoustID)
Jika file lagu Anda bernama `Track 01.mp3` atau `Lagu Viral Tanpa Judul.mp3` sehingga pencarian nama gagal, gunakan fitur scan suara:
1. Pilih file yang ada di kolom kiri (Unmatched Files).
2. Klik tombol **Scan** di menu atas.
3. Picard akan mendengarkan beberapa detik frekuensi file audio tersebut, menghasilkan kode sidik jari suara AcoustID, lalu mencocokkannya ke server database.
4. Jika cocok, lagu akan otomatis bergeser ke kolom kanan dalam format album resmi lengkap dengan tahun, genre, penerbit, dan gambar cover art aslinya.

---

## Langkah 5: Menyimpan Hasil Tagging
1. Pastikan Anda meninjau hasil pencocokan di kolom sebelah kanan.
2. Klik kanan pada album atau lagu di kolom kanan, lalu pilih **Save** (atau tekan tombol `Ctrl + S`).
3. Picard akan menuliskan tag metadata resmi tersebut langsung ke dalam file audio Anda secara permanen.
4. Setelah selesai, lagu Anda siap dipindahkan ke folder siaran aktif `00_ON_AIR_READY`.
