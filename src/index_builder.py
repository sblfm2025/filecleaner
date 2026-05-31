"""
src/index_builder.py — Modul Generator Katalog & Playlist M3U v3.0
==================================================================
Membangun katalog master CSV/XLSX/JSON dan file indeks playlist M3U
di folder 20_INDEX_CATALOG/ tanpa menduplikasi berkas fisik.

Prinsip:
  - 1 Berkas Fisik = 1 Lokasi Fisik di Master Folder.
  - Playlist M3U berfungsi sebagai pointer logis untuk kebutuhan broadcast radio.
  - Pengelompokan dinamis berdasarkan Genre, Mood, Dekade, Bahasa, dan Artis Terpopuler.
"""

import os
import re
import csv
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Tuple

from src.utils import load_json_config
from src.report_writer import write_csv_report, convert_csv_to_xlsx
from src.audio_classifier import _detect_language

logger = logging.getLogger("RADIO_MUSIC_CLEANER")

# Kolom katalog master radio v3.0
CATALOG_COLUMNS = [
    "file_id", "filename", "relative_path", "absolute_path",
    "media_type", "master_bucket", "target_folder", "confidence_score",
    "artist_tag", "title_tag", "album_tag", "genre_tag", "year_tag",
    "duration_seconds", "duration_readable", "bitrate", "sample_rate",
    "file_size_mb", "added_time"
]


def build_master_catalog(
    final_output_dir: str = "data/output/RADIO_AUDIO_MASTER_LIBRARY",
    logs_dir: str = "data/logs",
    catalog_dir: str = "data/output/RADIO_AUDIO_MASTER_LIBRARY/99_MASTER_CATALOG_DATABASE"
) -> List[Dict[str, Any]]:
    """
    Membuat katalog basis data master CSV, XLSX, dan JSON dengan memindai berkas audio fisik
    yang telah tersusun di dalam folder output master.
    """
    logger.info("=== Memulai Pembangunan Katalog Master Radio v3.0 ===")
    os.makedirs(catalog_dir, exist_ok=True)

    # Membaca file sorting report jika ada sebagai referensi data asli & metadata
    sorting_report_path = os.path.join(logs_dir, "folder_sorting_report.csv")
    sorting_data_map: Dict[str, Dict[str, Any]] = {}
    if os.path.exists(sorting_report_path):
        try:
            with open(sorting_report_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    dest = row.get("actual_dest_path", "")
                    if dest:
                        sorting_data_map[os.path.abspath(dest)] = row
        except Exception as e:
            logger.error(f"Gagal memuat laporan sortir: {e}")

    # Membaca file scan report juga untuk detail audio (bitrate, sample rate, dll)
    scan_report_path = os.path.join(logs_dir, "audio_scan_report.csv")
    scan_data_map: Dict[str, Dict[str, Any]] = {}
    if os.path.exists(scan_report_path):
        try:
            with open(scan_report_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    fname = row.get("clean_filename_suggestion", "") or row.get("filename", "")
                    if fname:
                        scan_data_map[fname] = row
        except Exception as e:
            logger.error(f"Gagal memuat laporan scan: {e}")

    # Pindai folder output secara fisik untuk memastikan sinkronisasi data nyata
    supported_extensions = {".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg", ".wma"}
    catalog_records: List[Dict[str, Any]] = []
    file_id_counter = 1

    # Kita lewati folder katalog database, bad audio, dan index playlist agar tidak masuk katalog musik
    exclude_folders = {
        "99_MASTER_CATALOG_DATABASE", 
        "92_BAD_AUDIO", 
        "20_INDEX_CATALOG",
        "90_NEEDS_REVIEW"
    }

    for root, dirs, files in os.walk(final_output_dir):
        # Filter folder yang dikecualikan di level teratas
        rel_root = os.path.relpath(root, final_output_dir)
        top_folder = rel_root.split(os.sep)[0] if rel_root != "." else ""
        if top_folder in exclude_folders:
            continue

        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext not in supported_extensions:
                continue

            abs_path = os.path.abspath(os.path.join(root, f))
            rel_path = os.path.relpath(abs_path, final_output_dir)
            
            # Cari informasi metadata dari sort report atau scan report
            sort_info = sorting_data_map.get(abs_path, {})
            filename_key = os.path.basename(abs_path)
            scan_info = scan_data_map.get(filename_key, {})

            # Ekstrak data metadata dasar
            artist = sort_info.get("artist_tag") or scan_info.get("artist_tag", "")
            title = sort_info.get("title_tag") or scan_info.get("title_tag", "")
            album = scan_info.get("album_tag", "")
            genre = scan_info.get("genre_tag", "")
            year = scan_info.get("year_tag", "")
            
            # Jika tag kosong, coba deteksi dari penamaan file "Artis - Judul"
            if not artist or not title:
                name_no_ext = os.path.splitext(f)[0]
                if " - " in name_no_ext:
                    parts = name_no_ext.split(" - ", 1)
                    artist = artist or parts[0].strip()
                    title = title or parts[1].strip()

            # Detail teknis audio
            duration_sec = 0.0
            try:
                duration_sec = float(scan_info.get("duration_seconds") or 0.0)
            except ValueError:
                pass
            duration_read = scan_info.get("duration_readable", "00:00")
            bitrate = scan_info.get("bitrate", "")
            sample_rate = scan_info.get("sample_rate", "")
            
            # Ukuran berkas
            size_mb = 0.0
            try:
                size_mb = os.path.getsize(abs_path) / (1024 * 1024)
            except OSError:
                try:
                    size_mb = float(scan_info.get("file_size_mb") or 0.0)
                except ValueError:
                    pass

            # Tambahkan record
            catalog_row = {
                "file_id": f"ID-{file_id_counter:05d}",
                "filename": f,
                "relative_path": rel_path.replace("\\", "/"),
                "absolute_path": abs_path,
                "media_type": sort_info.get("media_type") or "MUSIC",
                "master_bucket": sort_info.get("master_bucket") or rel_path.split(os.sep)[0],
                "target_folder": sort_info.get("target_folder") or os.path.dirname(rel_path).replace("\\", "/"),
                "confidence_score": sort_info.get("confidence_score") or 100,
                "artist_tag": artist.strip(),
                "title_tag": title.strip(),
                "album_tag": album.strip(),
                "genre_tag": genre.strip(),
                "year_tag": year.strip(),
                "duration_seconds": round(duration_sec, 2),
                "duration_readable": duration_read,
                "bitrate": bitrate,
                "sample_rate": sample_rate,
                "file_size_mb": round(size_mb, 2),
                "added_time": datetime.now().isoformat()
            }
            catalog_records.append(catalog_row)
            file_id_counter += 1

    # Tulis file database
    csv_path = os.path.join(catalog_dir, "music_catalog_master.csv")
    xlsx_path = os.path.join(catalog_dir, "music_catalog_master.xlsx")
    json_path = os.path.join(catalog_dir, "music_catalog_master.json")

    # CSV & XLSX
    write_csv_report(catalog_records, csv_path, CATALOG_COLUMNS)
    convert_csv_to_xlsx(csv_path, xlsx_path)

    # JSON
    try:
        with open(json_path, mode='w', encoding='utf-8') as f:
            json.dump(catalog_records, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Gagal menulis database JSON: {e}")

    logger.info(f"Katalog master selesai dibuat: {len(catalog_records)} lagu terdaftar.")
    return catalog_records


def generate_index_playlists(
    catalog_records: List[Dict[str, Any]],
    final_output_dir: str = "data/output/RADIO_AUDIO_MASTER_LIBRARY",
    index_dir: str = "data/output/RADIO_AUDIO_MASTER_LIBRARY/20_INDEX_CATALOG"
) -> Dict[str, int]:
    """
    Membangun file M3U playlists pointer logis di folder 20_INDEX_CATALOG/
    berdasarkan pengelompokan artis, genre, mood, dekade, dan bahasa.
    """
    logger.info("=== Memulai Pembangunan Index Playlist M3U v3.0 ===")
    os.makedirs(index_dir, exist_ok=True)

    # Muat konfigurasi aturan indeks
    genre_rules = load_json_config("config/classification/genre_index_rules.json", {})
    mood_rules = load_json_config("config/classification/mood_index_rules.json", {})
    intl_rules = load_json_config("config/classification/international_keywords.json", {})

    genre_map = genre_rules.get("genre_to_index_folder", {})
    decade_map = genre_rules.get("decade_to_index_folder", {})
    language_map = genre_rules.get("language_to_index_folder", {})
    mood_map = mood_rules.get("mood_keyword_to_index", {})
    energy_map = mood_rules.get("energy_keyword_to_index", {})
    rotation_map = mood_rules.get("rotation_keyword_to_index", {})

    # Penampung data playlist
    playlists: Dict[str, List[Dict[str, Any]]] = {}

    # Statistik pencatatan artis
    artist_songs: Dict[str, List[Dict[str, Any]]] = {}

    for row in catalog_records:
        artist = row.get("artist_tag", "")
        title = row.get("title_tag", "")
        filename = row.get("filename", "")
        genre = row.get("genre_tag", "").lower()
        year_str = row.get("year_tag", "")
        
        # Lokasi playlist relatif agar M3U bersifat portabel
        # Karena folder M3U berada di final_output_dir/20_INDEX_CATALOG/Subfolder/Nama.m3u
        # Pointer path ke file audio di final_output_dir adalah: ../../[relative_path]
        rel_audio_path = "../../" + row.get("relative_path", "")

        entry = {
            "title": title or filename,
            "artist": artist,
            "duration": row.get("duration_seconds", 0),
            "duration_readable": row.get("duration_readable", "0:00"),
            "path": rel_audio_path
        }

        # ── 1. INDEKS ARTIS (Minimal 3 lagu per artis) ──────────────────────
        if artist and artist.lower() not in ("unknown", "various", "vario", ""):
            artist_clean = artist.strip()
            artist_songs.setdefault(artist_clean, []).append(entry)

        # ── 2. INDEKS GENRE ──────────────────────────────────────────────────
        genre_matched = False
        for g_kw, target_m3u in genre_map.items():
            if g_kw in genre:
                playlists.setdefault(target_m3u, []).append(entry)
                genre_matched = True
                break
        
        # Fallback genre jika tidak ada yang cocok
        if not genre_matched and row.get("media_type") == "MUSIC":
            playlists.setdefault("02_GENRE_INDEX/Lain_Lain.m3u", []).append(entry)

        # ── 3. INDEKS MOOD (Kata kunci di judul/nama file) ─────────────────
        text_to_search = f"{title} {filename}".lower()
        for target_m3u, keywords in mood_map.items():
            for kw in keywords:
                if re.search(r'(?<![a-z])' + re.escape(kw.lower()) + r'(?![a-z])', text_to_search):
                    playlists.setdefault(target_m3u, []).append(entry)
                    break

        # ── 4. INDEKS DEKADE / TAHUN ──────────────────────────────────────────
        if year_str and re.match(r'^\d{4}$', year_str):
            year = int(year_str)
            if year >= 2020:
                playlists.setdefault(decade_map.get("2020s", "04_DECADE_YEAR_INDEX/2020s.m3u"), []).append(entry)
            elif year >= 2010:
                playlists.setdefault(decade_map.get("2010s", "04_DECADE_YEAR_INDEX/2010s.m3u"), []).append(entry)
            elif year >= 2000:
                playlists.setdefault(decade_map.get("2000s", "04_DECADE_YEAR_INDEX/2000s.m3u"), []).append(entry)
            elif year >= 1990:
                playlists.setdefault(decade_map.get("1990s", "04_DECADE_YEAR_INDEX/1990s.m3u"), []).append(entry)
            elif year >= 1980:
                playlists.setdefault(decade_map.get("1980s", "04_DECADE_YEAR_INDEX/1980s.m3u"), []).append(entry)
            elif year >= 1970:
                playlists.setdefault(decade_map.get("1970s", "04_DECADE_YEAR_INDEX/1970s.m3u"), []).append(entry)
            else:
                playlists.setdefault(decade_map.get("older", "04_DECADE_YEAR_INDEX/Classic_Pre1970.m3u"), []).append(entry)

        # ── 5. INDEKS BAHASA ─────────────────────────────────────────────────
        lang = _detect_language(f"{artist} {title}", intl_rules)
        if lang == "ID":
            playlists.setdefault(language_map.get("ID", "05_LANGUAGE_INDEX/Indonesian.m3u"), []).append(entry)
        elif lang == "EN":
            playlists.setdefault(language_map.get("EN", "05_LANGUAGE_INDEX/English.m3u"), []).append(entry)
        elif row.get("master_bucket") == "02_MASTER_LOCAL_REGIONAL":
            playlists.setdefault(language_map.get("LOCAL", "05_LANGUAGE_INDEX/Local_Regional.m3u"), []).append(entry)
        else:
            playlists.setdefault(language_map.get("MIXED", "05_LANGUAGE_INDEX/Mixed_Language.m3u"), []).append(entry)

        # ── 6. INDEKS ENERGI ─────────────────────────────────────────────────
        energy_matched = False
        for target_m3u, keywords in energy_map.items():
            for kw in keywords:
                if kw.lower() in text_to_search:
                    playlists.setdefault(target_m3u, []).append(entry)
                    energy_matched = True
                    break
        if not energy_matched:
            # Default ke Medium Energy
            playlists.setdefault("06_ENERGY_INDEX/Medium_Energy.m3u", []).append(entry)

        # ── 7. INDEKS ROTASI ─────────────────────────────────────────────────
        rotation_matched = False
        for target_m3u, keywords in rotation_map.items():
            for kw in keywords:
                if kw.lower() in text_to_search:
                    playlists.setdefault(target_m3u, []).append(entry)
                    rotation_matched = True
                    break
        if not rotation_matched:
            playlists.setdefault("12_ROTATION_LEVEL_INDEX/Regular_Rotation.m3u", []).append(entry)

    # Proses penulisan playlist Artis (Syarat: >= 3 lagu)
    for artist_name, entries in artist_songs.items():
        if len(entries) >= 3:
            # Sanitasi nama artis agar aman sebagai nama berkas
            safe_artist = re.sub(r'[<>:"/\\|?*]', '_', artist_name)[:50].strip()
            playlists[f"01_ARTIST_INDEX/{safe_artist}.m3u"] = entries

    # Statistik hasil penulisan
    written_counts = {}
    total_playlist_files = 0

    for m3u_rel_path, entries in playlists.items():
        if not entries:
            continue
        
        full_m3u_path = os.path.join(index_dir, m3u_rel_path)
        os.makedirs(os.path.dirname(full_m3u_path), exist_ok=True)

        try:
            with open(full_m3u_path, mode='w', encoding='utf-8') as f:
                f.write("#EXTM3U\n")
                for e in entries:
                    disp = f"{e['artist']} - {e['title']}" if e['artist'] else e['title']
                    duration_sec = int(e['duration']) if e['duration'] > 0 else -1
                    f.write(f"#EXTINF:{duration_sec},{disp}\n")
                    f.write(f"{e['path']}\n")
            
            # Catat statistik
            top_folder = m3u_rel_path.split("/")[0]
            written_counts[top_folder] = written_counts.get(top_folder, 0) + 1
            total_playlist_files += 1
        except Exception as e:
            logger.error(f"Gagal menulis file playlist {full_m3u_path}: {e}")

    logger.info(
        f"=== Playlist selesai dibuat. Total: {total_playlist_files} file. "
        f"Distribusi: {', '.join([f'{k}: {v}' for k, v in written_counts.items()])} ==="
    )

    return {k: v for k, v in written_counts.items()}
