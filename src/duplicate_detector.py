import os
import logging
from typing import List, Dict, Any, Tuple

try:
    from rapidfuzz import fuzz
except ImportError:
    fuzz = None

# Fallback ke difflib jika rapidfuzz tidak terinstal
if fuzz is None:
    import difflib
    class FakeFuzz:
        @staticmethod
        def ratio(s1: str, s2: str) -> float:
            return difflib.SequenceMatcher(None, s1, s2).ratio() * 100
    fuzz = FakeFuzz

def calculate_string_similarity(s1: str, s2: str) -> float:
    """Menghitung nilai persentase kemiripan antara dua buah string (0-100)."""
    if not s1 or not s2:
        return 0.0
    return float(fuzz.ratio(s1.lower().strip(), s2.lower().strip()))

def detect_duplicates_in_list(file_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Memindai daftar rekam data file audio untuk mendeteksi dugaan duplikat.
    Kriteria deteksi:
    1. Tag Artist & Title sama persis (jika ada).
    2. Nama file yang sudah dibersihkan sama persis.
    3. Durasi sama persis DAN ukuran file mirip.
    4. Nama file bersih mirip (>90%) DAN durasi mirip (selisih <= 3 detik).
    
    Mengembalikan daftar dugaan duplikat yang dikelompokkan dengan format laporan.
    """
    duplicates_report = []
    n = len(file_records)
    if n <= 1:
        return duplicates_report

    # Simpan indeks file yang sudah dianalisis agar tidak double report
    reported_pairs = set()
    group_counter = 1

    for i in range(n):
        f1 = file_records[i]
        f1_path = f1.get("source_path") or f1.get("original_path", "")
        f1_name, _ = os.path.splitext(os.path.basename(f1_path))
        f1_size = f1.get("file_size_mb", 0.0)
        f1_dur = f1.get("duration_seconds", 0.0)
        f1_artist = f1.get("artist_tag", "").strip()
        f1_title = f1.get("title_tag", "").strip()
        
        # Kelompokkan dengan file lain di depan
        group_members = []
        
        for j in range(i + 1, n):
            f2 = file_records[j]
            f2_path = f2.get("source_path") or f2.get("original_path", "")
            f2_name, _ = os.path.splitext(os.path.basename(f2_path))
            f2_size = f2.get("file_size_mb", 0.0)
            f2_dur = f2.get("duration_seconds", 0.0)
            f2_artist = f2.get("artist_tag", "").strip()
            f2_title = f2.get("title_tag", "").strip()

            pair_key = tuple(sorted([f1_path, f2_path]))
            if pair_key in reported_pairs:
                continue

            is_duplicate = False
            reason = ""
            similarity = 100.0
            
            # Kriteria 1: Tag Artist dan Title terisi dan sama persis
            if f1_artist and f1_title and f2_artist and f2_title:
                if f1_artist.lower() == f2_artist.lower() and f1_title.lower() == f2_title.lower():
                    is_duplicate = True
                    reason = "DUPLIKAT_TAG_SAMA"

            # Kriteria 2: Nama file bersih sama persis
            if not is_duplicate and f1_name.lower() == f2_name.lower() and f1_name:
                is_duplicate = True
                reason = "DUPLIKAT_NAMA_SAMA"

            # Kriteria 3: Durasi sama persis (selisih < 0.5s) DAN ukuran file mirip (selisih < 0.2MB) (minimal > 5 detik)
            if not is_duplicate and f1_dur > 5.0 and f2_dur > 5.0:
                if abs(f1_dur - f2_dur) < 0.5 and abs(f1_size - f2_size) < 0.2:
                    is_duplicate = True
                    reason = "DUPLIKAT_DURASI_DAN_UKURAN_SAMA"

            # Kriteria 4: Fuzzy matching nama file (>90%) DAN durasi mirip (selisih <= 3 detik) (minimal > 5 detik)
            if not is_duplicate and f1_dur > 5.0 and f2_dur > 5.0:
                if abs(f1_dur - f2_dur) <= 3.0:
                    sim = calculate_string_similarity(f1_name, f2_name)
                    if sim >= 90.0:
                        is_duplicate = True
                        reason = "DUPLIKAT_NAMA_MIRIP"
                        similarity = sim

            if is_duplicate:
                reported_pairs.add(pair_key)
                if not group_members:
                    group_members.append((f1, "Berkas Asli / Referensi", 100.0))
                group_members.append((f2, reason, similarity))

        # Jika ditemukan duplikat untuk berkas f1
        if group_members:
            # Tulis semua anggota ke laporan duplikat
            for file_data, reason_status, sim_score in group_members:
                path = file_data.get("source_path") or file_data.get("original_path", "")
                duplicates_report.append({
                    "group_id": f"DUP_GROUP_{group_counter:04d}",
                    "file_path": path,
                    "filename": os.path.basename(path),
                    "artist": file_data.get("artist_tag", ""),
                    "title": file_data.get("title_tag", ""),
                    "duration_seconds": file_data.get("duration_seconds", 0.0),
                    "file_size_mb": file_data.get("file_size_mb", 0.0),
                    "similarity_score": sim_score,
                    "duplicate_reason": reason_status,
                    "recommended_action": "CEK_MANUAL_JANGAN_HAPUS_OTOMATIS"
                })
            group_counter += 1

    return duplicates_report
