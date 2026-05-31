"""
src/playlist_exporter.py — Modul Pengekspor Daftar Putar RadioBoss v4.0
======================================================================
Mengekspor playlist logis pointer M3U dari basis data katalog master
khusus untuk software penyiaran radio (RadioBoss, dll) tanpa duplikasi file fisik.

Struktur Output:
  - 30_PLAYLIST_EXPORT/03_ROTATION_PLAYLIST/
    - Heavy_Rotation.m3u (Tahun >= 2024)
    - Medium_Rotation.m3u (Tahun 2020-2023)
    - Gold.m3u (Tahun < 2020)
  - 30_PLAYLIST_EXPORT/04_SPECIAL_EVENT_PLAYLIST/
"""

import os
import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger("RADIO_MUSIC_CLEANER")


def export_playlists_for_radioboss(
    catalog_records: List[Dict[str, Any]],
    final_output_dir: str = "data/output/RADIO_AUDIO_MASTER_LIBRARY",
    playlist_dir: str = "data/output/RADIO_AUDIO_MASTER_LIBRARY/30_PLAYLIST_EXPORT"
) -> Dict[str, int]:
    """
    Membangun playlist pointer M3U terkelompok untuk kebutuhan siaran RadioBoss stasiun radio.
    """
    logger.info("=== Memulai Ekspor Daftar Putar Siaran RadioBoss v4.0 ===")
    os.makedirs(playlist_dir, exist_ok=True)

    # Subfolder tujuan playlist
    rotation_dir = os.path.join(playlist_dir, "03_ROTATION_PLAYLIST")
    special_dir = os.path.join(playlist_dir, "04_SPECIAL_EVENT_PLAYLIST")
    backup_dir = os.path.join(playlist_dir, "05_BACKUP_PLAYLIST")

    for d in (rotation_dir, special_dir, backup_dir):
        os.makedirs(d, exist_ok=True)

    # Penampung lagu per kategori rotasi
    heavy_entries: List[Dict[str, Any]] = []  # Hits baru (Tahun >= 2024)
    medium_entries: List[Dict[str, Any]] = [] # Reguler (Tahun 2020-2023)
    gold_entries: List[Dict[str, Any]] = []   # Lawas (Tahun < 2020)
    backup_entries: List[Dict[str, Any]] = [] # Religi / Lokal backup

    for row in catalog_records:
        artist = row.get("artist_tag", "")
        title = row.get("title_tag", "")
        filename = row.get("filename", "")
        year_str = row.get("year_tag", "")
        rel_path = row.get("relative_path", "")
        media_type = row.get("media_type", "MUSIC")

        # Buat jalur relatif dari folder playlist ke file audio
        # M3U ditaruh di 30_PLAYLIST_EXPORT/Subfolder/Nama.m3u
        # Pointer path ke file audio di root: ../../[relative_path]
        rel_audio_path = "../../" + rel_path

        entry = {
            "title": title or filename,
            "artist": artist,
            "duration": row.get("duration_seconds", 0),
            "path": rel_audio_path
        }

        # Saring file non-musik (skip jingle/iklan komersial agar tidak masuk playlist rotasi otomatis)
        if media_type in ("COMMERCIAL_AD", "PUBLIC_SERVICE", "RADIO_ASSET"):
            continue

        # Klasifikasikan rotasi berdasarkan tahun rilis
        if year_str and re.match(r'^\d{4}$', year_str):
            try:
                year = int(year_str)
            except ValueError:
                year = 2020
                
            if year >= 2024:
                heavy_entries.append(entry)
            elif year >= 2020:
                medium_entries.append(entry)
            else:
                gold_entries.append(entry)
        else:
            # Fallback tahun kosong masuk reguler
            medium_entries.append(entry)

        # Masukkan ke backup playlist jika religi/lokal
        if media_type in ("RELIGIOUS_MUSIC", "LOCAL_REGIONAL_MUSIC"):
            backup_entries.append(entry)

    # Daftar playlist yang akan ditulis
    playlist_targets = [
        (os.path.join(rotation_dir, "Heavy_Rotation.m3u"), heavy_entries, "Heavy Rotation (hits baru >= 2024)"),
        (os.path.join(rotation_dir, "Medium_Rotation.m3u"), medium_entries, "Medium Rotation (reguler 2020-2023)"),
        (os.path.join(rotation_dir, "Gold.m3u"), gold_entries, "Gold (klasik < 2020)"),
        (os.path.join(backup_dir, "Backup_Music.m3u"), backup_entries, "Backup Music (religi/lokal)")
    ]

    export_stats = {}
    total_playlists = 0

    for path, entries, desc in playlist_targets:
        if not entries:
            logger.debug(f"[PLAYLIST] Melewati ekspor {desc} karena kosong.")
            continue

        try:
            with open(path, mode='w', encoding='utf-8') as f:
                f.write("#EXTM3U\n")
                for e in entries:
                    disp = f"{e['artist']} - {e['title']}" if e['artist'] else e['title']
                    duration_sec = int(float(e['duration'])) if e['duration'] else -1
                    f.write(f"#EXTINF:{duration_sec},{disp}\n")
                    f.write(f"{e['path']}\n")
            
            p_name = os.path.basename(path)
            export_stats[p_name] = len(entries)
            total_playlists += 1
            logger.info(f"[PLAYLIST] Sukses mengekspor {p_name}: {len(entries)} pointer lagu.")
        except Exception as e:
            logger.error(f"[PLAYLIST] Gagal mengekspor playlist {path}: {e}")

    logger.info(f"=== Ekspor playlist selesai: {total_playlists} berkas M3U RadioBoss siap pakai. ===")
    return export_stats
