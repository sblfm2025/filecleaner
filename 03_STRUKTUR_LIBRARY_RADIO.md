# 03 — Struktur Library Audio Radio Publik Lokal

Hasil akhir sistem harus diarahkan ke struktur berikut:

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
│
├── 01_MUSIK_LOKAL_DAERAH/
│   ├── Bugis/
│   ├── Makassar/
│   ├── Mandar/
│   ├── Toraja/
│   └── Artis_Lokal_Pinrang/
│
├── 02_MUSIK_INDONESIA/
│   ├── Pop_Indonesia/
│   ├── Dangdut/
│   ├── Religi/
│   ├── Nostalgia/
│   └── Lagu_Anak_Remaja/
│
├── 03_MUSIK_INTERNASIONAL/
│   ├── Western_Pop/
│   ├── Classic_Hits/
│   ├── KPop/
│   └── Soundtrack/
│
├── 04_NON_MUSIK_SIARAN/
│   ├── Jingle_Station_ID/
│   ├── Bumper_Program/
│   ├── Iklan/
│   ├── ILM_Layanan_Publik/
│   ├── Newsbed_Talkshow/
│   └── Event_Khusus/
│
├── 05_PROGRAM_REKAMAN/
│   ├── Talkshow/
│   ├── Wawancara/
│   ├── Berita_Lokal/
│   ├── Podcast/
│   └── Event_Off_Air/
│
├── 06_ROTASI_PLAYLIST/
│   ├── Pagi/
│   ├── Siang/
│   ├── Sore/
│   ├── Malam/
│   ├── Weekend/
│   ├── Lagu_Baru/
│   ├── Lagu_Lokal_Prioritas/
│   └── Emergency_Playlist/
│
├── 90_PERLU_DICEK/
├── 91_DUPLIKAT_DIDUGA/
├── 92_AUDIO_BERMASALAH/
└── 99_ARSIP_LAMA/
```

## 1. 00_ON_AIR_READY

Folder ini hanya untuk file yang sudah aman dipakai siaran.

Syarat file masuk folder ini:

- nama file rapi,
- metadata dasar cukup jelas,
- file bisa diputar,
- tidak terindikasi rusak,
- tidak ambigu,
- bukan duplikat berat.

Jangan masukkan file meragukan ke sini.

## 2. 01_MUSIK_LOKAL_DAERAH

Untuk memperkuat identitas radio lokal.

Subfolder:

```text
Bugis
Makassar
Mandar
Toraja
Artis_Lokal_Pinrang
```

Jika keyword lokal ditemukan di nama file atau genre, arahkan ke sini.

Contoh:

```text
Artis Lokal Pinrang - Judul Lagu.mp3
Penyanyi Bugis - Judul Lagu.mp3
```

## 3. 02_MUSIK_INDONESIA

Untuk lagu nasional.

Subfolder:

```text
Pop_Indonesia
Dangdut
Religi
Nostalgia
Lagu_Anak_Remaja
```

Jika tidak ada informasi cukup untuk genre, tetapi nama file jelas `Artis - Judul`, default boleh masuk:

```text
02_MUSIK_INDONESIA/Pop_Indonesia
```

Namun jika ragu, masukkan ke `90_PERLU_DICEK`.

## 4. 03_MUSIK_INTERNASIONAL

Untuk lagu luar negeri:

```text
Western_Pop
Classic_Hits
KPop
Soundtrack
```

Jangan terlalu banyak subfolder internasional agar operator tidak bingung.

## 5. 04_NON_MUSIK_SIARAN

Untuk audio non-lagu:

```text
Jingle_Station_ID
Bumper_Program
Iklan
ILM_Layanan_Publik
Newsbed_Talkshow
Event_Khusus
```

Prefix penting:

```text
JINGLE -
BUMPER -
IKLAN -
ILM -
INFO -
NEWSBED -
OPENING -
CLOSING -
SWEEPER -
CALLSIGN -
```

## 6. 05_PROGRAM_REKAMAN

Untuk rekaman siaran dan konten panjang:

```text
Talkshow
Wawancara
Berita_Lokal
Podcast
Event_Off_Air
```

Format nama file program:

```text
YYYY-MM-DD - Nama Program - Tema - Narasumber.mp3
```

Contoh:

```text
2026-05-31 - Dialog Publik - Pelayanan Kesehatan Gratis - PKM Malimpung.mp3
```

## 7. 06_ROTASI_PLAYLIST

Untuk kumpulan siap playlist:

```text
Pagi
Siang
Sore
Malam
Weekend
Lagu_Baru
Lagu_Lokal_Prioritas
Emergency_Playlist
```

Catatan: folder ini boleh berisi copy atau shortcut tergantung kebutuhan. Untuk versi awal, cukup siapkan folder kosong.

## 8. 90_PERLU_DICEK

Masukkan file ke sini jika:

- nama tidak jelas,
- metadata kosong,
- durasi aneh,
- ada teks `unknown`,
- nama file seperti `Track 01`,
- file dari WhatsApp,
- format tidak lazim,
- sistem tidak yakin.

## 9. 91_DUPLIKAT_DIDUGA

Untuk kandidat duplikat.

Jangan hapus otomatis.

## 10. 92_AUDIO_BERMASALAH

Untuk file:

- corrupt,
- gagal dibaca,
- durasi 0,
- suara terlalu pendek,
- file tidak bisa diputar,
- metadata error,
- path bermasalah.

## 11. 99_ARSIP_LAMA

Untuk arsip lama yang belum dipakai aktif tetapi tidak ingin dihapus.
