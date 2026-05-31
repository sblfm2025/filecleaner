# 05 — Spesifikasi Konfigurasi JSON

Semua aturan utama harus diletakkan di folder:

```text
config/
```

Agar operator/developer bisa memperbaiki aturan tanpa menyentuh kode utama.

## 1. cleaner_rules.json

File:

```text
config/cleaner_rules.json
```

Isi:

```json
{
  "remove_phrases": [
    "official music video",
    "official video",
    "official audio",
    "music video",
    "video lirik",
    "lyric video",
    "lyrics",
    "lyric",
    "lirik",
    "download lagu",
    "download mp3",
    "mp3 gratis",
    "full album",
    "audio spectrum",
    "hd",
    "hq",
    "320kbps",
    "128kbps",
    "256kbps",
    "tiktok viral",
    "tik tok viral",
    "viral tiktok",
    "viral tik tok",
    "terbaru",
    "terpopuler",
    "lagu terbaru",
    "lagu viral",
    "no copyright",
    "free download",
    "ytmp3",
    "youtube",
    "converted"
  ],
  "replace_chars": {
    "_": " ",
    "–": "-",
    "—": "-",
    "|": "-",
    "~": " ",
    "%20": " "
  },
  "remove_brackets_content_when_contains": [
    "official",
    "lyrics",
    "lyric",
    "lirik",
    "video",
    "hd",
    "hq",
    "download",
    "viral",
    "youtube",
    "ytmp3"
  ],
  "preserve_brackets_content_when_contains": [
    "acoustic",
    "remix",
    "live",
    "radio edit",
    "cover",
    "instrumental",
    "karaoke",
    "original",
    "clean version",
    "dangdut",
    "koplo"
  ],
  "windows_forbidden_chars": ["<", ">", ":", "\"", "/", "\\", "|", "?", "*"],
  "max_filename_length": 180
}
```

## 2. folder_mapping.json

File:

```text
config/folder_mapping.json
```

Isi:

```json
{
  "prefix_mapping": {
    "JINGLE -": "04_NON_MUSIK_SIARAN/Jingle_Station_ID",
    "SWEEPER -": "04_NON_MUSIK_SIARAN/Jingle_Station_ID",
    "CALLSIGN -": "04_NON_MUSIK_SIARAN/Jingle_Station_ID",
    "BUMPER -": "04_NON_MUSIK_SIARAN/Bumper_Program",
    "IKLAN -": "04_NON_MUSIK_SIARAN/Iklan",
    "ILM -": "04_NON_MUSIK_SIARAN/ILM_Layanan_Publik",
    "INFO -": "04_NON_MUSIK_SIARAN/ILM_Layanan_Publik",
    "NEWSBED -": "04_NON_MUSIK_SIARAN/Newsbed_Talkshow",
    "OPENING -": "04_NON_MUSIK_SIARAN/Newsbed_Talkshow",
    "CLOSING -": "04_NON_MUSIK_SIARAN/Newsbed_Talkshow",
    "VOXPOP -": "05_PROGRAM_REKAMAN/Wawancara",
    "EVENT -": "04_NON_MUSIK_SIARAN/Event_Khusus"
  },
  "keyword_mapping": {
    "bugis": "01_MUSIK_LOKAL_DAERAH/Bugis",
    "makassar": "01_MUSIK_LOKAL_DAERAH/Makassar",
    "mandar": "01_MUSIK_LOKAL_DAERAH/Mandar",
    "toraja": "01_MUSIK_LOKAL_DAERAH/Toraja",
    "pinrang": "01_MUSIK_LOKAL_DAERAH/Artis_Lokal_Pinrang",
    "dangdut": "02_MUSIK_INDONESIA/Dangdut",
    "koplo": "02_MUSIK_INDONESIA/Dangdut",
    "sholawat": "02_MUSIK_INDONESIA/Religi",
    "religi": "02_MUSIK_INDONESIA/Religi",
    "ramadan": "04_NON_MUSIK_SIARAN/Event_Khusus",
    "talkshow": "05_PROGRAM_REKAMAN/Talkshow",
    "wawancara": "05_PROGRAM_REKAMAN/Wawancara",
    "podcast": "05_PROGRAM_REKAMAN/Podcast"
  },
  "default_music_folder": "02_MUSIK_INDONESIA/Pop_Indonesia",
  "needs_review_folder": "90_PERLU_DICEK",
  "duplicate_folder": "91_DUPLIKAT_DIDUGA",
  "bad_audio_folder": "92_AUDIO_BERMASALAH"
}
```

## 3. metadata_defaults.json

File:

```text
config/metadata_defaults.json
```

Isi:

```json
{
  "default_album": "Radio SBL Library",
  "default_comment": "Processed by RADIO_MUSIC_CLEANER",
  "default_genre_music": "Musik",
  "default_genre_local": "Musik Lokal Daerah",
  "default_genre_jingle": "Jingle",
  "default_genre_bumper": "Bumper",
  "default_genre_iklan": "Iklan",
  "default_genre_ilm": "Iklan Layanan Masyarakat",
  "default_genre_program": "Program Rekaman",
  "default_artist_unknown": "UNKNOWN",
  "overwrite_existing_tags": false
}
```

## 4. batch_settings.json

File:

```text
config/batch_settings.json
```

Isi:

```json
{
  "batch_mode": true,
  "max_batch_size_gb": 50,
  "max_files_per_batch": 5000,
  "dry_run_default": true,
  "resume_enabled": true,
  "skip_completed_files": true,
  "copy_instead_of_move": true,
  "allow_delete": false,
  "allow_overwrite": false,
  "input_dir": "data/input",
  "input_batch_dir": "data/input_batch",
  "output_dir": "data/output",
  "output_batch_dir": "data/output_batch",
  "logs_dir": "data/logs"
}
```

## 5. Prinsip Pembacaan Config

Developer harus membuat fungsi utilitas:

```python
load_json_config(path)
```

Jika file config tidak ditemukan:

- buat default,
- tulis warning,
- jangan crash.

Jika JSON invalid:

- tampilkan error yang jelas,
- jangan lanjut ke apply mode,
- masih boleh menjalankan scan basic.
