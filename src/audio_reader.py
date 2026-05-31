import os
import logging
from typing import Dict, Any

try:
    import mutagen
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3, TIT2, TPE1, TALB, TCON, TDRC, TYER
except ImportError:
    mutagen = None

def format_duration(seconds: float) -> str:
    """Mengubah durasi detik menjadi format HH:MM:SS atau MM:SS."""
    if seconds <= 0:
        return "00:00"
    total_seconds = int(round(seconds))
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"

def read_audio_metadata(file_path: str) -> Dict[str, Any]:
    """
    Membaca informasi teknis dan tag metadata dasar dari file audio.
    Mendukung format umum seperti MP3, WAV, FLAC, M4A, OGG, dll.
    """
    result = {
        "duration_seconds": 0.0,
        "duration_readable": "00:00",
        "bitrate": 0,          # dalam kbps
        "sample_rate": 0,      # dalam Hz
        "title_tag": "",
        "artist_tag": "",
        "album_tag": "",
        "genre_tag": "",
        "year_tag": "",
        "is_valid": False,
        "error_message": ""
    }
    
    if not os.path.exists(file_path):
        result["error_message"] = "File tidak ditemukan"
        return result

    if mutagen is None:
        result["error_message"] = "Pustaka mutagen tidak terinstal"
        return result

    try:
        audio = mutagen.File(file_path)
        if audio is None:
            # Kadang mutagen mengembalikan None untuk format yang tidak dikenal/corrupt
            result["error_message"] = "Format file tidak didukung atau file corrupt"
            return result
        
        result["is_valid"] = True
        
        # 1. Baca Informasi Teknis
        if audio.info:
            if hasattr(audio.info, "length"):
                result["duration_seconds"] = float(audio.info.length)
                result["duration_readable"] = format_duration(audio.info.length)
            
            if hasattr(audio.info, "bitrate") and audio.info.bitrate:
                # Bitrate dari mutagen biasanya dalam bps, ubah ke kbps
                result["bitrate"] = int(audio.info.bitrate // 1000)
                
            if hasattr(audio.info, "sample_rate") and audio.info.sample_rate:
                result["sample_rate"] = int(audio.info.sample_rate)

        # 2. Baca Tag Metadata Dasar
        tags = audio.tags
        if tags:
            # Kasus khusus untuk MP3 ID3 tags
            if isinstance(tags, ID3):
                # Ekstrak tag dengan frame ID3
                title_frame = tags.get("TIT2")
                if title_frame:
                    result["title_tag"] = str(title_frame.text[0]) if title_frame.text else str(title_frame)
                    
                artist_frame = tags.get("TPE1")
                if artist_frame:
                    result["artist_tag"] = str(artist_frame.text[0]) if artist_frame.text else str(artist_frame)
                    
                album_frame = tags.get("TALB")
                if album_frame:
                    result["album_tag"] = str(album_frame.text[0]) if album_frame.text else str(album_frame)
                    
                genre_frame = tags.get("TCON")
                if genre_frame:
                    result["genre_tag"] = str(genre_frame.text[0]) if genre_frame.text else str(genre_frame)
                    
                year_frame = tags.get("TDRC") or tags.get("TYER")
                if year_frame:
                    result["year_tag"] = str(year_frame.text[0]) if year_frame.text else str(year_frame)
            else:
                # Kasus umum untuk format non-MP3 (FLAC, M4A, OGG, dll. yang menggunakan key-value standar)
                # Helper untuk mengambil nilai kunci case-insensitive
                def get_tag_value(keys):
                    for k in keys:
                        # Beberapa format menyimpan tag sebagai dictionary list
                        val = tags.get(k) or tags.get(k.upper()) or tags.get(k.lower())
                        if val:
                            if isinstance(val, list):
                                return str(val[0])
                            return str(val)
                    return ""
                
                result["title_tag"] = get_tag_value(["title", "tit2"])
                result["artist_tag"] = get_tag_value(["artist", "tpe1"])
                result["album_tag"] = get_tag_value(["album", "talb"])
                result["genre_tag"] = get_tag_value(["genre", "tcon"])
                result["year_tag"] = get_tag_value(["date", "year", "tyer", "tdrc"])

        # Bersihkan spasi berlebih pada metadata
        for key in ["title_tag", "artist_tag", "album_tag", "genre_tag", "year_tag"]:
            if result[key]:
                result[key] = result[key].strip()

    except Exception as e:
        result["is_valid"] = False
        result["error_message"] = str(e)
        logging.error(f"Gagal membaca metadata untuk file {file_path}: {e}")
        
    return result
