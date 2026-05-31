import os
import logging
from typing import Dict, Any, Tuple

try:
    import mutagen
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3, TIT2, TPE1, TALB, TCON, COMM
except ImportError:
    mutagen = None

from src.safe_file_ops import make_windows_safe_path

def write_mp3_metadata(file_path: str, tags_to_write: Dict[str, str], overwrite: bool) -> bool:
    """Menulis metadata khusus untuk file MP3 menggunakan ID3 tag."""
    try:
        safe_path = make_windows_safe_path(file_path)
        
        # Coba buka berkas MP3
        try:
            audio = MP3(safe_path)
        except Exception:
            # Jika berkas MP3 tidak memiliki header ID3 yang valid
            audio = MP3(safe_path)
            audio.add_tags()
            
        if audio.tags is None:
            audio.add_tags()
            
        tags = audio.tags
        
        # Tulis/perbarui tag ID3
        if "title" in tags_to_write and tags_to_write["title"]:
            if overwrite or "TIT2" not in tags:
                tags["TIT2"] = TIT2(encoding=3, text=tags_to_write["title"])
                
        if "artist" in tags_to_write and tags_to_write["artist"]:
            if overwrite or "TPE1" not in tags:
                tags["TPE1"] = TPE1(encoding=3, text=tags_to_write["artist"])
                
        if "album" in tags_to_write and tags_to_write["album"]:
            if overwrite or "TALB" not in tags:
                tags["TALB"] = TALB(encoding=3, text=tags_to_write["album"])
                
        if "genre" in tags_to_write and tags_to_write["genre"]:
            if overwrite or "TCON" not in tags:
                tags["TCON"] = TCON(encoding=3, text=tags_to_write["genre"])
                
        if "comment" in tags_to_write and tags_to_write["comment"]:
            # Cari frame COMM yang sudah ada
            has_comm = False
            for k in tags.keys():
                if k.startswith("COMM"):
                    has_comm = True
                    break
            if overwrite or not has_comm:
                # Hapus COMM lama jika ada dan overwrite aktif
                if overwrite:
                    comm_keys = [k for k in tags.keys() if k.startswith("COMM")]
                    for k in comm_keys:
                        del tags[k]
                tags.add(COMM(encoding=3, lang="eng", desc="comment", text=[tags_to_write["comment"]]))
                
        audio.save()
        return True
    except Exception as e:
        logging.error(f"Gagal menulis ID3 tag ke {file_path}: {e}")
        return False

def write_generic_metadata(file_path: str, tags_to_write: Dict[str, str], overwrite: bool) -> bool:
    """Menulis metadata generic untuk format non-MP3 (FLAC, M4A, OGG, dll.)."""
    try:
        safe_path = make_windows_safe_path(file_path)
        audio = mutagen.File(safe_path)
        if audio is None:
            return False
            
        tags = audio.tags
        if tags is None:
            # Format audio tidak mendukung penyimpanan tag mutagen secara default (misalnya WAV)
            return False
            
        def get_actual_key(k: str) -> str:
            """Mendapatkan kunci case-insensitive yang ada di tag file."""
            for tk in tags.keys():
                if tk.lower() == k.lower():
                    return tk
            return k

        # Pemetaan nama kunci standar
        key_mapping = {
            "title": "title",
            "artist": "artist",
            "album": "album",
            "genre": "genre",
            "comment": "comment"
        }
        
        # M4A/MP4 menggunakan kode kunci khusus (misalnya \xa9nam untuk title)
        # Jika mutagen memuat objek MP4Tags, kita harus mengikuti aturan tersebut.
        # Namun mutagen.File biasanya menangani key-value standar secara internal.
        
        for key, val in tags_to_write.items():
            if not val:
                continue
            std_key = key_mapping.get(key, key)
            actual_key = get_actual_key(std_key)
            
            if overwrite or actual_key not in tags:
                # Sebagian besar tag mutagen non-MP3 menyimpan nilai berupa list string
                tags[actual_key] = [val]
                
        audio.save()
        return True
    except Exception as e:
        logging.error(f"Gagal menulis generic tag ke {file_path}: {e}")
        return False

def write_basic_metadata(
    file_path: str,
    artist: str,
    title: str,
    defaults: Dict[str, Any],
    suggested_genre: str = ""
) -> Tuple[str, str]:
    """
    Menulis metadata dasar ke file audio di target_path.
    Mengembalikan tuple: (status, notes)
    """
    if mutagen is None:
        return "SKIPPED", "Pustaka mutagen tidak tersedia"
        
    if not os.path.exists(file_path):
        return "ERROR", "File tidak ditemukan"

    _, ext = os.path.splitext(file_path.lower())
    overwrite = defaults.get("overwrite_existing_tags", False)
    
    # 1. Tentukan nilai tag yang akan ditulis
    tags_to_write = {
        "title": title,
        "artist": artist,
        "album": defaults.get("default_album", "Radio SBL Library"),
        "comment": defaults.get("default_comment", "Processed by RADIO_MUSIC_CLEANER"),
        "genre": suggested_genre or defaults.get("default_genre_music", "Musik")
    }
    
    # 2. Tangani file WAV (WAV tidak didukung penulisan tag andal oleh mutagen standar)
    if ext == ".wav":
        return "SKIPPED", "Format WAV tidak mendukung penulisan tag mutagen standar secara andal"

    # 3. Lakukan penulisan tag berdasarkan tipe file
    success = False
    if ext == ".mp3":
        success = write_mp3_metadata(file_path, tags_to_write, overwrite)
    else:
        success = write_generic_metadata(file_path, tags_to_write, overwrite)
        
    if success:
        notes = []
        if artist: notes.append(f"Artist={artist}")
        if title: notes.append(f"Title={title}")
        return "SUCCESS", f"Tags berhasil ditulis: {', '.join(notes)}"
    else:
        return "FAILED", "Gagal menulis metadata tag ke berkas (kemungkinan format tidak mendukung)"
