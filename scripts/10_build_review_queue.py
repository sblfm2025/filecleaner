"""
scripts/10_build_review_queue.py — Pemicu Penyusunan Draf Antrean Tinjauan v4.0
================================================================================
Skrip CLI stasiun radio untuk menjalankan siklus penyusunan draf antrean tinjauan operator.
Menggabungkan data sortir fisik, data usulan metadata AcoustID + MusicBrainz,
dan menyusunnya menjadi draf keputusan final sebelum operator meninjau.

Penggunaan:
    python scripts/10_build_review_queue.py
"""

import os
import sys
import logging

# Pastikan root workspace masuk sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils import setup_logger
from src.review_queue import build_review_queue_draft

logger = logging.getLogger("RADIO_MUSIC_CLEANER")


def main():
    """Fungsi entri utama skrip CLI."""
    setup_logger()
    logger.info("======================================================================")
    logger.info("      MEMULAI PENYUSUNAN DRAF ANTREAN TINJAUAN OPERATOR v4.0")
    logger.info("======================================================================")

    logs_dir = "data/logs"
    results = build_review_queue_draft(logs_dir=logs_dir)

    if results:
        logger.info(f"[OK] Sukses memproses {len(results)} berkas ke dalam review queue.")
    else:
        logger.warning("[WARN] Tidak ada berkas yang dimasukkan ke antrean review.")

    logger.info("======================================================================")
    logger.info("      PROSES PENYUSUNAN DRAF ANTREAN TINJAUAN SELESAI DENGAN SUKSES!")
    logger.info("======================================================================")


if __name__ == "__main__":
    main()
