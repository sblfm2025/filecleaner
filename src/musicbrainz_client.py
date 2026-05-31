"""
src/musicbrainz_client.py — Klien Independen MusicBrainz API v4.0
==================================================================
Melakukan kueri HTTP langsung ke MusicBrainz XML/JSON Web Service (v2)
untuk menarik metadata resmi lagu berdasarkan Recording ID.

Bebas Dependensi: Menggunakan pustaka bawaan Python (urllib.request & json).
Mematuhi Aturan: Menyertakan User-Agent unik stasiun radio dan jeda pembatasan laju.
"""

import json
import time
import logging
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

logger = logging.getLogger("RADIO_MUSIC_CLEANER")

# User-Agent unik stasiun radio untuk mematuhi rate limit MusicBrainz (1 request/second)
_USER_AGENT = "SBLFMAudioLibraryManager/4.0 ( admin@sblfm.co.id )"
_LAST_REQUEST_TIME = 0.0


def query_musicbrainz_recording(recording_id: str) -> Optional[Dict[str, Any]]:
    """
    Melakukan kueri metadata perekaman (Recording) dari MusicBrainz.
    Mengembalikan Dict dengan kunci: suggested_artist, suggested_title, suggested_album, suggested_year, genre.
    """
    global _LAST_REQUEST_TIME
    if not recording_id:
        return None

    # Terapkan jeda 1 detik untuk mematuhi kebijakan rate limit MusicBrainz
    elapsed = time.time() - _LAST_REQUEST_TIME
    if elapsed < 1.0:
        time.sleep(1.0 - elapsed)

    url = f"https://musicbrainz.org/ws/2/recording/{recording_id}?fmt=json&inc=artists+releases+tags"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": _USER_AGENT,
            "Accept": "application/json"
        }
    )

    _LAST_REQUEST_TIME = time.time()
    logger.debug(f"[MUSICBRAINZ] Mengirim lookup URL: {url}")

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            # Ekstrak data metadata dasar
            title = data.get("title", "")
            
            # 1. Ekstrak artis
            artist_parts = []
            for credit in data.get("artist-credit", []):
                artist_obj = credit.get("artist", {})
                name = artist_obj.get("name", "")
                join_phrase = credit.get("joinphrase", "")
                if name:
                    artist_parts.append(name + join_phrase)
            artist = "".join(artist_parts).strip() if artist_parts else ""

            # 2. Ekstrak rilis album terpopuler
            album = ""
            year = ""
            releases = data.get("releases", [])
            if releases:
                # Ambil rilis pertama sebagai acuan utama
                best_release = releases[0]
                album = best_release.get("title", "")
                date_str = best_release.get("date", "")
                if date_str and len(date_str) >= 4:
                    year = date_str[:4]  # Ambil tahun saja (YYYY)

            # 3. Ekstrak genre tag terbanyak
            genre = ""
            tags = data.get("tags", [])
            if tags:
                # Urutkan berdasarkan hit count tag terbanyak
                sorted_tags = sorted(tags, key=lambda x: x.get("count", 0), reverse=True)
                genre = sorted_tags[0].get("name", "").title()

            result = {
                "musicbrainz_recording_id": recording_id,
                "suggested_artist": artist,
                "suggested_title": title,
                "suggested_album": album,
                "suggested_year": year,
                "suggested_genre": genre
            }
            logger.info(f"[MUSICBRAINZ] Ditemukan: {artist} - {title} ({year})")
            return result

    except urllib.error.HTTPError as e:
        logger.error(f"[MUSICBRAINZ] HTTP Error {e.code} saat lookup {recording_id}: {e.reason}")
        # Jika kena rate limit (429), beri jeda lebih panjang
        if e.code == 429:
            time.sleep(2.0)
    except urllib.error.URLError as e:
        logger.error(f"[MUSICBRAINZ] URL Error saat lookup {recording_id}: {e.reason}")
    except Exception as e:
        logger.error(f"[MUSICBRAINZ] Kesalahan tidak terduga saat lookup {recording_id}: {e}")

    return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Tes lookup dengan Recording ID lagu populer (Metallica - Enter Sandman)
    test_id = "ecb8fb0f-870b-4654-8e1c-b26a63212879"
    print(f"Menguji lookup MusicBrainz untuk ID: {test_id}...")
    res = query_musicbrainz_recording(test_id)
    print("Hasil:", res)
