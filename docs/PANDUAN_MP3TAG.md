# Panduan Finishing Menggunakan Mp3tag

Meskipun **RADIO_MUSIC_CLEANER** telah membersihkan nama file dan mengisi metadata dasar, langkah finishing manual tetap penting untuk memastikan kelengkapan tag audio (seperti gambar Cover Art, Genre yang lebih spesifik, dan Tahun rilis). **Mp3tag** adalah software gratis terbaik di Windows untuk kebutuhan ini.

---

## Langkah 1: Download & Instal Mp3tag
1. Unduh Mp3tag secara gratis di situs resminya: [mp3tag.de](https://www.mp3tag.de/en/download.html).
2. Instal aplikasi di PC Windows Anda seperti biasa.

---

## Langkah 2: Membuka Folder Output Library di Mp3tag
1. Buka aplikasi Mp3tag.
2. Klik menu **File** -> **Change Directory...** (atau tekan tombol kombinasi `Ctrl + D`).
3. Arahkan ke folder hasil penataan proyek Anda:
   ```text
   data/output/RADIO_AUDIO_LIBRARY/
   ```
4. Klik **Select Folder**. Mp3tag akan memuat seluruh daftar lagu di dalam library.

---

## Langkah 3: Melakukan Audit Tag yang Kosong
1. Anda bisa mengurutkan daftar lagu berdasarkan kolom **Artist** atau **Title** dengan mengklik header kolom tersebut.
2. File dengan kolom kosong menandakan tag metadatanya belum terisi (biasanya berasal dari file kategori `90_PERLU_DICEK`).
3. Untuk mengisi tag secara manual:
   - Klik pada lagu yang ingin diedit.
   - Isi field **Title**, **Artist**, **Album**, **Genre**, atau **Year** pada panel sebelah kiri.
   - Klik tombol **Save** (ikon disket biru di kiri atas) atau tekan `Ctrl + S`.

---

## Langkah 4: Auto-Tag dari Nama File (Filename to Tag)
Jika ada file dengan nama rapi seperti `Artis - Judul.mp3` namun tag metadatanya kosong, Anda bisa mengisinya secara massal:
1. Blok lagu-lagu tersebut di daftar.
2. Klik menu **Convert** -> **Filename - Tag** (atau tekan tombol `Alt + 2`).
3. Ketik format pattern berikut:
   ```text
   %artist% - %title%
   ```
4. Klik **OK**. Mp3tag akan langsung memindahkan nama artis dan judul dari nama file ke dalam tag metadata lagu secara instan untuk ratusan file sekaligus.

---

## Langkah 5: Mengunduh Cover Art & Tag Resmi Secara Online
Mp3tag menyediakan fitur pencarian metadata online gratis bawaan:
1. Pilih satu atau beberapa lagu resmi.
2. Klik menu **Tag Sources** di bagian atas.
3. Pilih sumber database, misalnya **MusicBrainz** atau **Discogs**.
4. Ikuti petunjuk pencarian untuk mencocokkan album dan mengunduh gambar sampul (Cover Art) lagu secara otomatis.
5. Jangan lupa klik **Save** setelah selesai.
