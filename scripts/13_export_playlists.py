"""
scripts/13_export_playlists.py — Pemicu Ekspor Daftar Putar Siaran RadioBoss v4.0
==================================================================================
Skrip CLI stasiun radio untuk memproses ekspor playlist logis pointer M3U
yang sangat ramah dan kompatibel dengan software siaran radio (RadioBoss, dll).

Membaca basis data katalog master, jika belum ada, ia memicu pembangunan
katalog master secara otomatis untuk menjamin kestabilan sistem.

Penggunaan:
    python scripts/13_export_playlists.py
"""

import os
import sys
import csv
import logging
from typing import Dict, Any, List

# Pastikan root workspace masuk sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils import setup_logger
from src.index_builder import build_master_catalog
from src.playlist_exporter import export_playlists_for_radioboss

logger = logging.getLogger("RADIO_MUSIC_CLEANER")


def main(
    final_output_dir: str = "data/output/RADIO_AUDIO_MASTER_LIBRARY",
    logs_dir: str = "data/logs"
) -> Dict[str, int]:
    """Fungsi utama untuk memicu ekspor playlist logis RadioBoss."""
    logger.info("======================================================================")
    logger.info("      MEMULAI PROSES EKSPOR PLAYLIST POINTER LOGIS RADIOBOSS v4.0")
    logger.info("======================================================================")

    catalog_csv_path = os.path.join(final_output_dir, "99_MASTER_CATALOG_DATABASE", "music_catalog_master.csv")
    catalog_records: List[Dict[str, Any]] = []

    # 1. Cek basis data katalog master
    if not os.path.exists(catalog_csv_path):
        logger.warning("[PLAYLIST] Basis data katalog master tidak ditemukan. Membangun katalog otomatis...")
        catalog_records = build_master_catalog(
            final_output_dir=final_output_dir,
            logs_dir=logs_dir
        )
    else:
        try:
            with open(catalog_csv_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                catalog_records = list(reader)
        except Exception as e:
            logger.error(f"[PLAYLIST] Gagal membaca katalog master: {e}")
            return {}

    if not catalog_records:
        logger.warning("[WARN] Katalog master kosong. Penulisan playlist siaran dilewati.")
        return {}

    # 2. Pemicu ekspor playlist logis M3U
    stats = export_playlists_for_radioboss(
        catalog_records=catalog_records,
        final_output_dir=final_output_dir
    )

    logger.info("======================================================================")
    logger.info("      PROSES EKSPOR PLAYLIST SIARAN SELESAI DENGAN SUKSES!")
    logger.info("======================================================================")
    
    return stats


if __name__ == "__main__":
    setup_logger()
    main()
