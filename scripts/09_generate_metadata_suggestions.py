"""
scripts/09_generate_metadata_suggestions.py — Pemicu Evaluasi Usulan Metadata v4.0
==================================================================================
Skrip CLI stasiun radio untuk menjalankan siklus evaluasi usulan metadata cerdas.
Menggabungkan data AcoustID, query MusicBrainz, dan mendeteksi konflik tag
sebelum disajikan ke dalam antrean tinjauan operator (review queue).

Penggunaan:
    python scripts/09_generate_metadata_suggestions.py
"""

import os
import sys
import logging

# Pastikan root workspace masuk sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils import setup_logger
from src.metadata_suggestion_engine import evaluate_metadata_suggestions

logger = logging.getLogger("RADIO_MUSIC_CLEANER")


def main():
    """Fungsi entri utama skrip CLI."""
    setup_logger()
    logger.info("======================================================================")
    logger.info("   MEMULAI EVALUASI USULAN METADATA ACUSTID + MUSICBRAINZ v4.0")
    logger.info("======================================================================")

    logs_dir = "data/logs"
    results = evaluate_metadata_suggestions(logs_dir=logs_dir)

    if results:
        logger.info(f"[OK] Sukses memproses {len(results)} berkas evaluasi usulan metadata.")
    else:
        logger.warning("[WARN] Tidak ada berkas lagu yang diproses untuk usulan metadata.")

    logger.info("======================================================================")
    logger.info("   PROSES EVALUASI USULAN METADATA SELESAI DENGAN SUKSES!")
    logger.info("======================================================================")


if __name__ == "__main__":
    main()
