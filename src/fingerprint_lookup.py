"""
src/fingerprint_lookup.py — Modul AcoustID Fingerprint Lookup v4.0
==================================================================
Mengekstrak sidik jari audio (fingerprint) berkas lagu resmi menggunakan
fpcalc (Chromaprint) dan mencocokkannya ke database AcoustID Web Service.

Fitur Keamanan:
  - Melacak executable fpcalc.exe secara dinamis pada OS Windows/Linux.
  - Melewati (skip) aman file non-musik (jingle, iklan, program, dll)
    dan file dengan durasi di luar 90-600 detik.
  - Memanggil AcoustID API via kueri POST untuk menghindari URI Too Long.
"""

import os
import csv
import json
import logging
import subprocess
import urllib.request
import urllib.parse
import urllib.error
from typing import Dict, Any, List, Optional, Tuple

from src.utils import load_json_config
from src.report_writer import write_csv_report, convert_csv_to_xlsx

logger = logging.getLogger("RADIO_MUSIC_CLEANER")

# API Key default stasiun radio SBL-FM untuk AcoustID
_ACOUSTID_CLIENT_API_KEY = "8XaBELxH5O"


def find_fpcalc_executable() -> Optional[str]:
    """
    Melacak keberadaan berkas executable fpcalc secara dinamis pada Windows/Linux.
    Mengembalikan absolute path fpcalc jika ditemukan, atau None.
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 1. Daftar lokasi pencarian di dalam proyek
    search_paths = [
        os.path.join(project_root, "bin", "fpcalc.exe"),
        os.path.join(project_root, "fpcalc.exe"),
        os.path.join(project_root, "bin", "fpcalc"),
        os.path.join(project_root, "fpcalc")
    ]

    for p in search_paths:
        if os.path.exists(p):
            logger.debug(f"[FINGERPRINT] fpcalc ditemukan di lokasi proyek: {p}")
            return p

    # 2. Cek apakah ada di PATH sistem menggunakan utility command 'where' (Windows) atau 'which' (Linux)
    try:
        cmd = "where" if os.name == 'nt' else "which"
        res = subprocess.check_output([cmd, "fpcalc"], stderr=subprocess.DEVNULL)
        p_path = res.decode('utf-8').strip().split('\n')[0].strip()
        if p_path and os.path.exists(p_path):
            logger.debug(f"[FINGERPRINT] fpcalc ditemukan di PATH sistem: {p_path}")
            return p_path
    except Exception:
        pass

    return None


def calculate_audio_fingerprint(filepath: str, fpcalc_path: str) -> Optional[Tuple[float, str]]:
    """
    Menjalankan subproses fpcalc untuk mengekstrak durasi dan string sidik jari audio berkas.
    Mengembalikan Tuple (duration_seconds, fingerprint_string) atau None.
    """
    if not filepath or not os.path.exists(filepath):
        logger.warning(f"[FINGERPRINT] Berkas tidak ditemukan: {filepath}")
        return None

    try:
        # Panggil fpcalc dengan parameter json
        cmd = [fpcalc_path, "-json", filepath]
        
        # Sembunyikan window shell pada Windows agar tidak mengganggu operator
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            startupinfo=startupinfo,
            timeout=30,
            check=True
        )

        data = json.loads(result.stdout.decode('utf-8'))
        duration = float(data.get("duration", 0))
        fingerprint = data.get("fingerprint", "")

        if duration > 0 and fingerprint:
            return duration, fingerprint
            
    except subprocess.TimeoutExpired:
        logger.error(f"[FINGERPRINT] Batas waktu pemrosesan fpcalc habis untuk {os.path.basename(filepath)}")
    except Exception as e:
        logger.error(f"[FINGERPRINT] Gagal mengekstrak sidik jari berkas {os.path.basename(filepath)}: {e}")

    return None


def lookup_acoustid(duration: float, fingerprint: str) -> Optional[Dict[str, Any]]:
    """
    Mengirimkan sidik jari audio ke AcoustID Web Service lookup API via kueri HTTP POST.
    Mengembalikan kecocokan terbaik (best match) atau None.
    """
    if not fingerprint or duration <= 0:
        return None

    url = "https://api.acoustid.org/v2/lookup"
    
    # Susun data POST (recordings+releases untuk meta lengkap)
    post_data = {
        "client": _ACOUSTID_CLIENT_API_KEY,
        "meta": "recordings releases",
        "duration": int(duration),
        "fingerprint": fingerprint
    }
    
    encoded_data = urllib.parse.urlencode(post_data).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=encoded_data,
        headers={
            "User-Agent": "SBLFMAudioLibraryManager/4.0 ( admin@sblfm.co.id )",
            "Content-Type": "application/x-www-form-urlencoded"
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            
            if res_data.get("status") != "ok":
                logger.warning(f"[ACOUSTID] API Response status tidak ok: {res_data.get('error')}")
                return None

            results = res_data.get("results", [])
            if not results:
                logger.info("[ACOUSTID] Tidak ada lagu yang cocok (no match).")
                return None

            # Ambil kecocokan pertama (skor tertinggi)
            best_match = results[0]
            acoustid_id = best_match.get("id", "")
            score = float(best_match.get("score", 0))

            recording_id = ""
            artist = ""
            title = ""
            album = ""
            year = ""

            recordings = best_match.get("recordings", [])
            if recordings:
                # Ambil perekaman dengan metadata paling lengkap
                best_rec = recordings[0]
                recording_id = best_rec.get("id", "")
                title = best_rec.get("title", "")
                
                # Ekstrak artis
                artists = best_rec.get("artists", [])
                if artists:
                    artist = " & ".join([a.get("name", "") for a in artists if a.get("name")])

                # Ekstrak album & tahun
                releases = best_rec.get("releases", [])
                if releases:
                    best_rel = releases[0]
                    album = best_rel.get("title", "")
                    date_str = best_rel.get("date", {})
                    if isinstance(date_str, dict):
                        year_val = date_str.get("year", "")
                        year = str(year_val) if year_val else ""
                    elif isinstance(date_str, str) and len(date_str) >= 4:
                        year = date_str[:4]

            match_data = {
                "acoustid": acoustid_id,
                "acoustid_score": round(score, 3),
                "musicbrainz_recording_id": recording_id,
                "suggested_artist": artist,
                "suggested_title": title,
                "suggested_album": album,
                "suggested_year": year
            }
            logger.info(f"[ACOUSTID] Cocok ({score:.2f}): {artist} - {title}")
            return match_data

    except urllib.error.HTTPError as e:
        logger.error(f"[ACOUSTID] HTTP Error {e.code} saat lookup: {e.reason}")
    except Exception as e:
        logger.error(f"[ACOUSTID] Kesalahan tidak terduga saat lookup AcoustID: {e}")

    return None


def is_eligible_for_fingerprint(
    media_type: str,
    duration_seconds: float,
    confidence_score: float,
    decision: str,
    filename: str
) -> Tuple[bool, str]:
    """
    Memeriksa kelayakan berkas audio untuk proses fingerprinting AcoustID stasiun radio.
    Mengembalikan Tuple (is_eligible, skip_reason).
    """
    # 1. Tolak tipe non-musik
    is_non_music = media_type in ("RADIO_ASSET", "COMMERCIAL_AD", "PUBLIC_SERVICE", "INSTRUMENTAL_BED", "PROGRAM_RECORDING")
    if is_non_music:
        return False, f"Aset non-musik ({media_type})"

    # 2. Tolak durasi di luar rentang 90 - 600 detik (1.5 menit s/d 10 menit)
    if duration_seconds < 90.0 or duration_seconds > 600.0:
        return False, f"Durasi tidak sesuai ({duration_seconds:.0f}s)"

    # 3. Cek prefix resmi yang kuat (skip pengaman)
    fname_lower = filename.lower()
    strong_prefixes = ("jingle-", "bumper-", "iklan-", "ads-", "ilm-", "psa-", "newsbed-", "sfx-", "stinger-", "talkshow-")
    if fname_lower.startswith(strong_prefixes):
        return False, "Prefix nama berkas non-musik kuat"

    # 4. Hanya proses file yang data metadatanya lemah/ragu
    # Jika rule-based classifier sudah sangat percaya diri (AUTO_SORT >= 85), tidak perlu fingerprint
    if decision == "AUTO_SORT" and confidence_score >= 85:
        return False, "Confidence rule-based sudah tinggi (AUTO_SORT)"

    return True, "Layak untuk fingerprint"
