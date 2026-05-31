# 07 — Aturan Metadata Audio

## 1. Tujuan Metadata

Metadata dipakai agar di aplikasi siaran seperti RadioBoss, penyiar dapat melihat:

- judul lagu,
- artis,
- album,
- genre,
- keterangan internal.

## 2. Metadata Minimal

Untuk lagu:

```text
Title   = Judul Lagu
Artist  = Nama Artis
Album   = Radio SBL Library
Genre   = Pop Indonesia / Dangdut / Religi / Musik Lokal Daerah / dst.
Comment = Processed by RADIO_MUSIC_CLEANER
```

Untuk jingle:

```text
Title   = Radio SBL Station ID 01
Artist  = Radio SBL
Album   = Jingle Radio SBL
Genre   = Jingle
Comment = Station ID
```

Untuk iklan:

```text
Title   = Nama Klien - Promo/Event - 30s
Artist  = Nama Klien
Album   = Iklan Radio SBL
Genre   = Iklan
Comment = Masa tayang jika diketahui
```

Untuk ILM:

```text
Title   = Cegah DBD
Artist  = Radio SBL / Instansi
Album   = Iklan Layanan Masyarakat
Genre   = ILM
Comment = Layanan publik
```

## 3. Aturan Jangan Overwrite

Default:

```text
overwrite_existing_tags = false
```

Artinya:

- jika Title sudah ada, jangan timpa,
- jika Artist sudah ada, jangan timpa,
- jika Album kosong, boleh isi default,
- jika Genre kosong, boleh isi default,
- jika Comment kosong, boleh isi default.

## 4. Deteksi dari Filename

Jika nama file:

```text
Andmesh - Cinta Luar Biasa.mp3
```

Maka:

```text
Artist = Andmesh
Title  = Cinta Luar Biasa
```

Jika nama file:

```text
JINGLE - Radio SBL Station ID 01.mp3
```

Maka jangan anggap `JINGLE` sebagai artis lagu. Gunakan aturan khusus non-musik.

## 5. File Ambigu

Jangan menulis tag otomatis jika nama file:

```text
Track 01.mp3
Audio WhatsApp.mp3
Unknown.mp3
Lagu Viral.mp3
New Recording.mp3
```

Masukkan ke:

```text
90_PERLU_DICEK
```

## 6. MP3 ID3

Untuk MP3, gunakan ID3 tag.

Developer harus menangani kondisi:

- file belum punya ID3,
- encoding teks,
- tag lama,
- error read/write.

Jika gagal tulis metadata, jangan crash. Catat ke log.

## 7. WAV dan Format Lain

Tidak semua format menyimpan metadata dengan cara yang sama.

Untuk WAV:

- jangan paksa metadata kompleks,
- jika mutagen tidak aman, cukup catat di laporan,
- rename file tetap bisa dilakukan.

## 8. Cover Art

Untuk tahap awal, jangan wajib memproses cover art.

Alasan:

- memperlambat proses,
- menambah ukuran file,
- rawan error,
- tidak penting untuk operasional radio.

Fitur cover art bisa menjadi pengembangan lanjutan.

## 9. Metadata untuk RadioBoss

Pastikan metadata dasar terbaca dengan format umum:

```text
Title
Artist
Album
Genre
Year/Date jika tersedia
Comment
```

Setelah output selesai, operator dapat membuka folder hasil di Mp3tag untuk finishing manual.
