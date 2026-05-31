import os
import shutil
import logging
from typing import Tuple

def make_windows_safe_path(path: str) -> str:
    """
    Mengubah path menjadi format Windows Long Path (\\?\) jika berjalan di Windows,
    untuk mencegah error batas panjang path 260 karakter.
    """
    abs_path = os.path.abspath(path)
    if os.name == 'nt':
        if not abs_path.startswith("\\\\?\\"):
            # Pastikan format pemisah path menggunakan backslash
            abs_path = abs_path.replace("/", "\\")
            return f"\\\\?\\{abs_path}"
    return abs_path

def generate_unique_filepath(dest_dir: str, filename: str) -> str:
    """
    Membuat nama file unik di direktori tujuan jika terjadi bentrokan nama.
    Contoh: "lagu.mp3" -> "lagu_1.mp3" -> "lagu_2.mp3"
    """
    name_part, ext = os.path.splitext(filename)
    target_path = os.path.join(dest_dir, filename)
    
    counter = 1
    # Kita periksa keberadaan file dengan path aman Windows
    while os.path.exists(make_windows_safe_path(target_path)):
        new_filename = f"{name_part}_{counter}{ext}"
        target_path = os.path.join(dest_dir, new_filename)
        counter += 1
        
    return target_path

def safe_copy_file(src_path: str, dest_dir: str, target_filename: str) -> Tuple[str, str]:
    """
    Menyalin file secara aman dari sumber ke direktori tujuan dengan nama baru.
    Menghindari overwrite dengan membuat nama file unik jika terjadi bentrokan.
    Mengembalikan tuple: (actual_target_path, status)
    """
    try:
        # Buat direktori tujuan jika belum ada
        os.makedirs(dest_dir, exist_ok=True)
        
        # Dapatkan path unik untuk file tujuan
        actual_target_path = generate_unique_filepath(dest_dir, target_filename)
        
        # Terapkan proteksi path panjang Windows
        safe_src = make_windows_safe_path(src_path)
        safe_dst = make_windows_safe_path(actual_target_path)
        
        # Salin file beserta metadata aslinya (shutil.copy2)
        shutil.copy2(safe_src, safe_dst)
        
        return actual_target_path, "SUCCESS"
    except Exception as e:
        logging.error(f"Gagal menyalin file dari {src_path} ke {dest_dir}: {e}")
        return "", f"ERROR: {str(e)}"
