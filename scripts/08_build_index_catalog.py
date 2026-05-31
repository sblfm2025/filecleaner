"""
scripts/08_build_index_catalog.py — Pembangun Katalog Master & Playlist M3U v3.0
=================================================================================
Skrip CLI untuk menjalankan proses pembangunan katalog master stasiun radio
dan memetakan seluruh playlist logis M3U di folder 20_INDEX_CATALOG/ secara dinamis.

Penggunaan:
    python scripts/08_build_index_catalog.py
"""

import os
import sys
import logging
from typing import Dict, Any

# Pastikan root workspace masuk sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils import setup_logger
from src.index_builder import build_master_catalog, generate_index_playlists

logger = logging.getLogger("RADIO_MUSIC_CLEANER")


def main(
    final_output_dir: str = "data/output/RADIO_AUDIO_MASTER_LIBRARY",
    logs_dir: str = "data/logs"
) -> Dict[str, Any]:
    """
    Fungsi utama untuk membangun katalog master radio dan playlist dinamis.
    """
    logger.info("======================================================================")
    logger.info("   MEMULAI PEMBANGUNAN KATALOG MASTER & PLAYLISTS M3U v3.0")
    logger.info("======================================================================")

    # 1. Bangun katalog master database CSV/XLSX/JSON
    catalog_records = build_master_catalog(
        final_output_dir=final_output_dir,
        logs_dir=logs_dir
    )

    if not catalog_records:
        logger.warning("Katalog master kosong atau tidak ada berkas musik fisik yang disortir.")
        return {"total_records": 0, "playlists_stats": {}}

    # 2. Bangun file pointer M3U playlists
    playlists_stats = generate_index_playlists(
        catalog_records=catalog_records,
        final_output_dir=final_output_dir
    )

    logger.info("======================================================================")
    logger.info("   PROSES PEMBANGUNAN KATALOG & PLAYLIST SELESAI DENGAN SUKSES!")
    logger.info("======================================================================")
    
    return {
        "total_records": len(catalog_records),
        "playlists_stats": playlists_stats
    }


if __name__ == "__main__":
    setup_logger()
    main()
