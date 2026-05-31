# Struktur Folder Hasil Akhir Penataan — RADIO_AUDIO_LIBRARY

Dokumen ini menjelaskan struktur folder kategori siaran radio lokal hasil keluaran dari **RADIO_MUSIC_CLEANER** yang terletak di `data/output/RADIO_AUDIO_LIBRARY/`.

---

## Gambaran Umum Folder Utama

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
├── 01_MUSIK_LOKAL_DAERAH/
│   ├── Bugis/
│   ├── Makassar/
│   ├── Mandar/
│   ├── Toraja/
│   └── Artis_Lokal_Pinrang/
├── 02_MUSIK_INDONESIA/
│   ├── Pop_Indonesia/
│   ├── Dangdut/
│   ├── Religi/
│   ├── Nostalgia/
│   └── Lagu_Anak_Remaja/
├── 03_MUSIK_INTERNASIONAL/
│   ├── Western_Pop/
│   ├── Classic_Hits/
│   ├── KPop/
│   └── Soundtrack/
├── 04_NON_MUSIK_SIARAN/
│   ├── Jingle_Station_ID/
│   ├── Bumper_Program/
│   ├── Iklan/
│   ├── ILM_Layanan_Publik/
│   ├── Newsbed_Talkshow/
│   └── Event_Khusus/
├── 05_PROGRAM_REKAMAN/
│   ├── Talkshow/
│   ├── Wawancara/
│   ├── Berita_Lokal/
│   ├── Podcast/
│   └── Event_Off_Air/
├── 90_PERLU_DICEK/
├── 91_DUPLIKAT_DIDUGA/
├── 92_AUDIO_BERMASALAH/
└── 99_ARSIP_LAMA/
```

---

## Deskripsi & Kriteria Folder Kategori

### 1. `00_ON_AIR_READY`
Folder ini merupakan **area steril** yang hanya boleh diisi oleh file yang sudah siap diputar di playlist siaran aktif.
- **Kriteria**: Nama file rapi, metadata tag Artist & Title terisi lengkap, berkas tidak rusak (corrupt), tidak ambigu, dan durasinya sesuai.
- **Catatan**: Tool tidak mengisi folder ini secara otomatis. Operator harus memeriksa berkas di folder kategori terlebih dahulu lalu memindahkannya secara manual ke sini demi keamanan kualitas siaran.

### 2. `01_MUSIK_LOKAL_DAERAH`
Folder khusus untuk musik-musik etnik lokal guna mendukung konten budaya daerah.
- **Subfolder**: Bugis, Makassar, Mandar, Toraja, Artis_Lokal_Pinrang.
- **Kriteria**: Terdeteksi kata kunci kedaerahan di nama file atau tag genre (misalnya kata `bugis`, `makassar`, `pinrang`).

### 3. `02_MUSIK_INDONESIA`
Folder utama untuk lagu-lagu berbahasa Indonesia skala nasional.
- **Subfolder**: Pop_Indonesia, Dangdut, Religi, Nostalgia, Lagu_Anak_Remaja.
- **Kriteria**: Lagu umum berbahasa Indonesia.
- **Fallback**: Jika file memiliki format `Artis - Judul` yang jelas namun genre-nya tidak terdefinisi secara khusus, secara default tool akan memasukkannya ke subfolder `Pop_Indonesia`.

### 4. `03_MUSIK_INTERNASIONAL`
Folder untuk lagu-lagu mancanegara (Barat, KPop, dll.).
- **Subfolder**: Western_Pop, Classic_Hits, KPop, Soundtrack.

### 5. `04_NON_MUSIK_SIARAN`
Kumpulan materi audio pendukung siaran (bukan lagu penuh).
- **Kriteria**: Terdeteksi berdasarkan prefix nama file:
  - `JINGLE -` ke `Jingle_Station_ID`
  - `BUMPER -` ke `Bumper_Program`
  - `IKLAN -` ke `Iklan`
  - `ILM -` atau `INFO -` ke `ILM_Layanan_Publik`
  - `NEWSBED -` ke `Newsbed_Talkshow`

### 6. `05_PROGRAM_REKAMAN`
Berisi file rekaman siaran lokal berdurasi panjang.
- **Subfolder**: Talkshow, Wawancara, Berita_Lokal, Podcast.

### 7. `90_PERLU_DICEK` (Fallback Utama)
Jika tool mendeteksi file yang ambigu (misalnya tidak memiliki pola nama `Artis - Judul` yang jelas, file dengan nama `Track 01.mp3`, rekaman kiriman WhatsApp, dll.), file tersebut akan dilemparkan ke sini agar operator memeriksanya secara manual.

### 8. `91_DUPLIKAT_DIDUGA`
Tempat penampungan salinan file terduga ganda. Memudahkan operator melakukan audit visual dan audit dengar sebelum melakukan penghapusan manual.

### 9. `92_AUDIO_BERMASALAH`
Folder penampungan berkas audio yang corrupt, ukuran 0 byte, durasi kosong, atau terjadi error perizinan saat dibaca oleh sistem.
