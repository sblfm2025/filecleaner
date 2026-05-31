"""
scripts/08_generate_index.py — Generator Index Genre/Artis (M3U & CSV)
=======================================================================
Membuat file indeks per genre dan per artis tanpa menyalin file audio fisik.
Output: data/index/by_genre/, by_artist/, by_decision/

Prinsip: Index adalah pointer ke file, bukan salinan file.
"""

import os
import csv
import logging
from typing import List, Dict, Any
from datetime import datetime

from src.utils import load_json_config, setup_logger
from src.report_writer import write_csv_report, convert_csv_to_xlsx


INDEX_REPORT_COLUMNS = [
    "filename", "original_path", "artist_tag", "title_tag", "genre_tag",
    "duration_readable", "confidence_score", "decision", "sorted_folder"
]


def generate_index(
    batch_id: str = "",
    final_output_dir: str = "data/output/RADIO_AUDIO_LIBRARY",
    logs_dir: str = "data/logs",
    index_dir: str = "data/index"
) -> Dict[str, int]:
    """
    Membuat file index genre, artis, dan decision berformat M3U dan CSV.
    Tidak menyalin file audio — hanya membuat pointer.
    """
    logger = logging.getLogger("RADIO_MUSIC_CLEANER")
    logger.info("=== Memulai Pembuatan Index Genre/Artis ===")

    os.makedirs(index_dir, exist_ok=True)

    # Muat data scan dan sortir
    scan_report_path = os.path.join(logs_dir, "audio_scan_report.csv")
    sort_report_path = os.path.join(logs_dir, "folder_sorting_report.csv")

    scan_rows: List[Dict[str, str]] = []
    sort_rows: List[Dict[str, str]] = []

    if os.path.exists(scan_report_path):
        with open(scan_report_path, encoding="utf-8") as f:
            scan_rows = list(csv.DictReader(f))

    if os.path.exists(sort_report_path):
        with open(sort_report_path, encoding="utf-8") as f:
            sort_rows = list(csv.DictReader(f))

    # Buat peta: original_path → data scan lengkap
    scan_map: Dict[str, Dict[str, str]] = {}
    for row in scan_rows:
        scan_map[row.get("original_path", "")] = row

    # Buat peta: original_path → target_path (lokasi final)
    target_map: Dict[str, str] = {}
    for row in sort_rows:
        src = row.get("source_path", "")
        tgt = row.get("target_path", "")
        if src and tgt and row.get("status") == "SUCCESS":
            # source_path di sort adalah file di output_batch, kita perlu cari original
            # Cari original yang cocok dengan nama file
            target_map[src] = tgt

    # Kumpulkan data untuk indeks
    index_by_genre: Dict[str, List[Dict]] = {}
    index_by_artist: Dict[str, List[Dict]] = {}
    index_by_decision: Dict[str, List[Dict]] = {}
    index_all: List[Dict] = []

    for sort_row in sort_rows:
        if sort_row.get("status") != "SUCCESS":
            continue

        src = sort_row.get("source_path", "")
        target_path = sort_row.get("target_path", "")
        sorted_folder = sort_row.get("sorted_folder", "")
        decision = sort_row.get("decision", "UNKNOWN")
        confidence = sort_row.get("confidence_score", "")
        filename = sort_row.get("new_filename", os.path.basename(target_path))

        # Cari metadata dari scan report
        # source_path di sort = target_path dari apply (output_batch)
        scan_info: Dict[str, str] = {}
        for orig_path, s_row in scan_map.items():
            if os.path.basename(orig_path) == os.path.basename(src) or \
               os.path.basename(s_row.get("clean_filename_suggestion", "")) == os.path.basename(src):
                scan_info = s_row
                break

        artist_tag = scan_info.get("artist_tag", "")
        title_tag = scan_info.get("title_tag", "")
        genre_tag = scan_info.get("genre_tag", "")
        duration = scan_info.get("duration_readable", "")

        entry = {
            "filename": filename,
            "original_path": target_path,  # lokasi final
            "artist_tag": artist_tag,
            "title_tag": title_tag,
            "genre_tag": genre_tag,
            "duration_readable": duration,
            "confidence_score": confidence,
            "decision": decision,
            "sorted_folder": sorted_folder
        }
        index_all.append(entry)

        # Indeks per genre (dari folder yang disortir)
        if sorted_folder:
            genre_key = sorted_folder.replace("/", "_").replace("\\", "_")
            index_by_genre.setdefault(genre_key, []).append(entry)

        # Indeks per artis (normalisasi)
        if artist_tag and artist_tag.lower() not in ["unknown", "various", "vario", ""]:
            artist_key = re.sub(r'[<>:"/\\|?*]', '_', artist_tag.strip())[:50]
            index_by_artist.setdefault(artist_key, []).append(entry)

        # Indeks per decision
        index_by_decision.setdefault(decision, []).append(entry)

    # ── TULIS INDEX ─────────────────────────────────────────────────────────
    stats = {"total": len(index_all), "genres": 0, "artists": 0, "decisions": 0}

    # 1. by_genre
    genre_dir = os.path.join(index_dir, "by_genre")
    os.makedirs(genre_dir, exist_ok=True)
    for genre_key, entries in index_by_genre.items():
        _write_m3u(os.path.join(genre_dir, f"{genre_key}.m3u"), entries)
        _write_index_csv(os.path.join(genre_dir, f"{genre_key}.csv"), entries)
        stats["genres"] += 1

    # 2. by_artist
    artist_dir = os.path.join(index_dir, "by_artist")
    os.makedirs(artist_dir, exist_ok=True)
    for artist_key, entries in index_by_artist.items():
        _write_m3u(os.path.join(artist_dir, f"{artist_key}.m3u"), entries)
        _write_index_csv(os.path.join(artist_dir, f"{artist_key}.csv"), entries)
        stats["artists"] += 1

    # 3. by_decision
    decision_dir = os.path.join(index_dir, "by_decision")
    os.makedirs(decision_dir, exist_ok=True)
    for dec_key, entries in index_by_decision.items():
        _write_m3u(os.path.join(decision_dir, f"{dec_key}.m3u"), entries)
        _write_index_csv(os.path.join(decision_dir, f"{dec_key}.csv"), entries)
        stats["decisions"] += 1

    # 4. Laporan classification_report
    clf_report_path = os.path.join(logs_dir, "classification_report.csv")
    _write_index_csv(clf_report_path, index_all)
    # Konversi ke XLSX
    try:
        from src.report_writer import convert_csv_to_xlsx
        convert_csv_to_xlsx(clf_report_path, clf_report_path.replace(".csv", ".xlsx"))
    except Exception as e:
        logger.warning(f"Gagal membuat classification_report.xlsx: {e}")

    logger.info(f"=== Index selesai: {stats['total']} berkas | {stats['genres']} genre | {stats['artists']} artis | {stats['decisions']} decision ===")
    logger.info(f"Laporan klasifikasi: {clf_report_path}")
    return stats


def _write_m3u(path: str, entries: List[Dict]) -> None:
    """Menulis file playlist M3U dari daftar entry."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            for e in entries:
                artist = e.get("artist_tag", "")
                title = e.get("title_tag", "") or e.get("filename", "")
                duration_str = e.get("duration_readable", "0:00")
                # Konversi MM:SS ke detik
                try:
                    parts = duration_str.split(":")
                    secs = int(parts[-1]) + int(parts[-2]) * 60 if len(parts) >= 2 else 0
                except Exception:
                    secs = -1
                display = f"{artist} - {title}" if artist else title
                f.write(f"#EXTINF:{secs},{display}\n")
                f.write(f"{e.get('original_path', '')}\n")
    except Exception as ex:
        logging.error(f"Gagal menulis M3U {path}: {ex}")


def _write_index_csv(path: str, entries: List[Dict]) -> None:
    """Menulis file CSV indeks dari daftar entry."""
    if not entries:
        return
    try:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=INDEX_REPORT_COLUMNS, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(entries)
    except Exception as ex:
        logging.error(f"Gagal menulis CSV {path}: {ex}")


# Impor re untuk sanitasi nama file
import re

if __name__ == "__main__":
    setup_logger()
    result = generate_index()
    print(f"Index selesai: {result}")
