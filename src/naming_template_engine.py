"""
src/naming_template_engine.py — Mesin Pola Penamaan Dinamis v4.0
================================================================
Memformat nama berkas audio stasiun radio secara fleksibel dan terstruktur
berdasarkan variabel pola template metadata.

Variabel yang didukung:
  - %artist% : Nama Artis
  - %title%  : Judul Lagu
  - %album%  : Nama Album
  - %year%   : Tahun Rilis
  - %genre%  : Genre
  - %ext%    : Ekstensi Berkas Asli (contoh: .mp3)
"""

import os
import re
from typing import Dict, Any

# Template default stasiun radio
DEFAULT_MUSIC_TEMPLATE = "%artist% - %title%%ext%"
DEFAULT_NON_MUSIC_TEMPLATE = "%title%%ext%"


def format_filename_by_template(
    template: str,
    metadata: Dict[str, Any],
    original_filename: str = ""
) -> str:
    """
    Memformat nama berkas audio stasiun radio menggunakan metadata tag dan string template.
    """
    if not template:
        template = DEFAULT_MUSIC_TEMPLATE

    # Ambil nilai metadata dengan fallback
    artist = str(metadata.get("artist_tag") or metadata.get("artist") or "").strip()
    title = str(metadata.get("title_tag") or metadata.get("title") or "").strip()
    album = str(metadata.get("album_tag") or metadata.get("album") or "").strip()
    year = str(metadata.get("year_tag") or metadata.get("year") or "").strip()
    genre = str(metadata.get("genre_tag") or metadata.get("genre") or "").strip()

    # Deteksi ekstensi berkas
    ext = ""
    if original_filename:
        ext = os.path.splitext(original_filename)[1].lower()
    if not ext:
        ext = ".mp3"  # Fallback default

    # Jika artis dan judul kosong, gunakan nama file asli tanpa ekstensi sebagai judul
    if not artist and not title and original_filename:
        title = os.path.splitext(original_filename)[0].strip()

    # Mapping pengganti pola
    replacements = {
        "%artist%": artist,
        "%title%": title,
        "%album%": album,
        "%year%": year,
        "%genre%": genre,
        "%ext%": ext
    }

    formatted = template
    for key, val in replacements.items():
        # Bersihkan karakter terlarang Windows pada nama file
        safe_val = re.sub(r'[<>:"/\\|?*]', '_', val) if val else ""
        formatted = formatted.replace(key, safe_val)

    # Bersihkan spasi ganda atau tanda hubung menggantung akibat penggantian kosong
    formatted = re.sub(r'\s+', ' ', formatted).strip()
    formatted = formatted.replace(" - - ", " - ")
    if formatted.startswith("- "):
        formatted = formatted[2:]
    if formatted.endswith(" -"):
        formatted = formatted[:-2]

    # Pastikan ekstensi tetap tersemat dengan benar di akhir nama file
    if not formatted.lower().endswith(ext.lower()):
        # Jika ekstensinya hilang akibat penggantian kosong, paksa sematkan
        # Bersihkan ekstensi dari karakter ilegal lalu gabungkan
        formatted_name_only = os.path.splitext(formatted)[0]
        formatted = formatted_name_only.strip() + ext

    # Jika nama file hasil format kosong/invalid, fallback ke original
    if not formatted or formatted == ext:
        formatted = original_filename if original_filename else f"Audio_Unnamed{ext}"

    return formatted
