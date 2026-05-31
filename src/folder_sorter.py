"""
src/folder_sorter.py — Wrapper Backward-Compatible
===================================================
DEPRECATED: Fungsi determine_target_folder di modul ini sekarang adalah
wrapper yang mendelegasikan ke audio_classifier.py (multi-stage classifier).

Modul ini dipertahankan agar skrip lama yang mungkin mengimpor
determine_target_folder tetap berjalan tanpa perubahan.

Untuk penggunaan baru, gunakan langsung:
  from src.audio_classifier import classify_audio
"""

import os
import re
import warnings
from typing import Dict, Any, Tuple
from src.audio_classifier import classify_audio_file
from src.utils import load_json_config


def determine_target_folder(
    filename: str,
    genre_tag: str,
    artist_tag: str,
    title_tag: str,
    mapping_config: Dict[str, Any],
    parent_folder: str = ""
) -> Tuple[str, str]:
    """
    [WRAPPER - DEPRECATED] Gunakan classify_audio_file() untuk penggunaan baru.

    Mendelegasikan ke classify_audio_file() dan mengembalikan:
    (target_folder, reason)

    Kompatibel dengan semua pemanggil lama.
    """
    warnings.warn(
        "determine_target_folder() is deprecated and will be removed. "
        "Use src.audio_classifier.classify_audio_file() instead.",
        DeprecationWarning,
        stacklevel=2
    )

    # Jalankan classifier multi-stage v3.0
    result = classify_audio_file(
        filename=filename,
        artist_tag=artist_tag,
        title_tag=title_tag,
        genre_tag=genre_tag,
        duration_seconds=None,  # durasi tidak tersedia di interface lama
        parent_folder=parent_folder
    )

    return result["target_folder"], result["reason"]


def is_likely_english_text(text: str) -> bool:
    """
    [DEPRECATED] Fungsi ini dipertahankan untuk kompatibilitas.
    Gunakan _detect_language() di audio_classifier.py untuk penggunaan baru.
    """
    if not text:
        return False

    classifier_config = load_json_config("config/classifier_config.json", {})
    words = set(re.sub(r'[^a-zA-Z\\s]', '', text.lower()).split())
    en_words = set(classifier_config.get("english_stopwords", []))
    id_words = set(classifier_config.get("indonesian_stopwords", []))
    en_count = len(words & en_words)
    id_count = len(words & id_words)
    return en_count > 0 and en_count >= id_count

