"""
test_manager.py — Test Suite Terpadu RADIO AUDIO LIBRARY MANAGER v4.0
======================================================================
Menguji seluruh integrasi AcoustID mock, metadata suggestion engine,
review queue, log operasi, dan rollback keselamatan secara atomik.

Menjamin keandalan sistem stasiun radio 100% lulus QA.
"""

import os
import sys
import unittest
import csv
import json
import shutil
from unittest.mock import patch, MagicMock

# Pastikan root workspace masuk sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils import load_json_config
from src.fingerprint_lookup import is_eligible_for_fingerprint
from src.metadata_suggestion_engine import evaluate_metadata_suggestions
from src.review_queue import build_review_queue_draft
from src.operation_log import log_operation
from src.rollback_manager import write_to_rollback_manifest, execute_rollback_for_file


class TestRadioLibraryManager(unittest.TestCase):
    
    def setUp(self):
        """Mempersiapkan folder pengujian sementara (sandbox)."""
        self.test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scratch", "test_sandbox")
        os.makedirs(self.test_dir, exist_ok=True)
        self.logs_dir = os.path.join(self.test_dir, "logs")
        os.makedirs(self.logs_dir, exist_ok=True)
        
        # Buat dummy files unik agar program tidak bentrok/crash
        self.dummy_source1 = os.path.join(self.test_dir, "dummy_source1.mp3")
        with open(self.dummy_source1, "wb") as f:
            f.write(b"ID3dummy_audio_bytes_1")
            
        self.dummy_source2 = os.path.join(self.test_dir, "dummy_source2.mp3")
        with open(self.dummy_source2, "wb") as f:
            f.write(b"ID3dummy_audio_bytes_2")
            
        self.dummy_dest = os.path.join(self.test_dir, "dummy_dest.mp3")
        
    def tearDown(self):
        """Membersihkan folder sandbox setelah pengujian selesai."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_fingerprint_eligibility(self):
        """Menguji kelayakan suatu lagu untuk diproses sidik jarinya."""
        # 1. Lagu resmi ambigu, tag kosong -> Layak
        eligible, reason = is_eligible_for_fingerprint(
            media_type="MUSIC",
            duration_seconds=180,
            confidence_score=45,
            decision="NEEDS_REVIEW",
            filename="Track 01.mp3"
        )
        self.assertTrue(eligible)
        
        # 2. Durasi terlalu pendek (jingle) -> Tidak layak
        eligible, reason = is_eligible_for_fingerprint(
            media_type="MUSIC",
            duration_seconds=30,
            confidence_score=45,
            decision="NEEDS_REVIEW",
            filename="Jingle Radio.mp3"
        )
        self.assertFalse(eligible)
        self.assertIn("durasi", reason.lower())
        
        # 3. Kategori non-musik (IKLAN) -> Tidak layak
        eligible, reason = is_eligible_for_fingerprint(
            media_type="COMMERCIAL_AD",
            duration_seconds=120,
            confidence_score=45,
            decision="NEEDS_REVIEW",
            filename="IKLAN Toko Baju.mp3"
        )
        self.assertFalse(eligible)
        self.assertIn("non-musik", reason.lower())

    @patch("src.metadata_suggestion_engine.query_musicbrainz_recording")
    def test_metadata_suggestion_engine(self, mock_query):
        """Menguji generator usulan metadata cerdas AcoustID + MusicBrainz."""
        # Setup mock untuk web service MusicBrainz
        mock_query.return_value = {
            "suggested_artist": "Judika",
            "suggested_title": "Aku Yang Tersakiti",
            "suggested_album": "Setengah Mati Merindu",
            "suggested_year": "2010",
            "suggested_genre": "Pop"
        }
        
        # 1. Buat dummy scan report
        scan_report = os.path.join(self.logs_dir, "audio_scan_report.csv")
        with open(scan_report, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "original_path", "filename", "media_type", "artist_tag", "title_tag", "album_tag", "genre_tag", "year_tag", "duration_seconds", "confidence_score", "decision"])
            # File 1: Musik dengan tag kosong
            writer.writerow(["FID-00001", self.dummy_source1, "track1.mp3", "MUSIC", "", "", "", "", "", "200", "30", "NEEDS_REVIEW"])
            # File 2: Musik yang konflik tag
            writer.writerow(["FID-00002", self.dummy_source2, "track2.mp3", "MUSIC", "Dewa 19", "Kangen", "", "", "", "240", "40", "NEEDS_REVIEW"])
            
        # 2. Buat dummy fingerprint report
        fp_report = os.path.join(self.logs_dir, "fingerprint_report.csv")
        with open(fp_report, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["file_id", "file_path", "filename", "fingerprint_status", "acoustid", "acoustid_score", "musicbrainz_recording_id", "suggested_artist", "suggested_title", "suggested_album", "suggested_year", "match_status", "skip_reason"])
            # File 1: Sukses match AcoustID skor tinggi (0.95)
            writer.writerow(["FID-00001", self.dummy_source1, "track1.mp3", "SUCCESS_ACOUSTID", "acoustid-1234", "0.95", "mb-rec-111", "Judika", "Aku Yang Tersakiti", "", "", "MATCHED", ""])
            # File 2: Sukses match AcoustID tapi konflik tag asli
            writer.writerow(["FID-00002", self.dummy_source2, "track2.mp3", "SUCCESS_ACOUSTID", "acoustid-5678", "0.92", "mb-rec-222", "Judika", "Aku Yang Tersakiti", "", "", "MATCHED", ""])

        # 3. Jalankan evaluasi suggestion engine
        results = evaluate_metadata_suggestions(logs_dir=self.logs_dir)
        self.assertEqual(len(results), 2)
        
        # Evaluasi File 1: Seharusnya AUTO_WRITE_EMPTY_TAGS (karena tag kosong dan skor tinggi)
        res_file1 = next(r for r in results if r["file_id"] == "FID-00001")
        self.assertEqual(res_file1["metadata_write_mode"], "AUTO_WRITE_EMPTY_TAGS")
        self.assertEqual(res_file1["suggested_artist"], "Judika")
        self.assertEqual(res_file1["suggested_title"], "Aku Yang Tersakiti")
        
        # Evaluasi File 2: Seharusnya REVIEW_CONFLICT (karena tag asli berbeda dengan usulan)
        res_file2 = next(r for r in results if r["file_id"] == "FID-00002")
        self.assertEqual(res_file2["metadata_write_mode"], "REVIEW_CONFLICT")
        self.assertEqual(res_file2["conflict_detected"], "YES")

    def test_review_queue_builder(self):
        """Menguji pembangun draf antrean review operator stasiun radio."""
        # 1. Buat dummy folder sorting report
        sort_report = os.path.join(self.logs_dir, "folder_sorting_report.csv")
        with open(sort_report, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["file_id", "current_batch_path", "filename", "media_type", "decision", "confidence_score", "artist_tag", "title_tag", "target_folder", "classification_reason"])
            # File 1: Sukses sort otomatis
            writer.writerow(["FID-00001", self.dummy_source1, "Judika - Aku Yang Tersakiti.mp3", "MUSIC", "AUTO_SORT", "95", "Judika", "Aku Yang Tersakiti", "01_MASTER_MUSIC/Pop_Indonesia", "Whitelist artis cocok"])
            # File 2: Butuh review
            writer.writerow(["FID-00002", self.dummy_source2, "track2.mp3", "MUSIC", "NEEDS_REVIEW", "40", "", "", "90_NEEDS_REVIEW", "Tag kosong"])

        # 2. Buat dummy metadata suggestions
        sug_report = os.path.join(self.logs_dir, "metadata_suggestions.csv")
        with open(sug_report, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["file_id", "file_path", "filename", "media_type", "current_artist", "current_title", "current_album", "current_genre", "current_year", "suggested_artist", "suggested_title", "suggested_album", "suggested_genre", "suggested_year", "musicbrainz_recording_id", "acoustid_score", "metadata_write_mode", "conflict_detected", "notes"])
            # File 1: Match sempurna
            writer.writerow(["FID-00001", self.dummy_source1, "Judika - Aku Yang Tersakiti.mp3", "MUSIC", "Judika", "Aku Yang Tersakiti", "", "", "", "Judika", "Aku Yang Tersakiti", "Setengah Mati Merindu", "Pop", "2010", "mb-rec-111", "0.95", "SUGGEST_ONLY", "NO", "Saran album"])
            # File 2: No match AcoustID
            writer.writerow(["FID-00002", self.dummy_source2, "track2.mp3", "MUSIC", "", "", "", "", "", "", "", "", "", "", "", "", "NO_MATCH", "NO", "AcoustID no match"])

        # 3. Bangun Review Queue
        results = build_review_queue_draft(logs_dir=self.logs_dir)
        self.assertEqual(len(results), 2)
        
        # File 1: Status disetujui otomatis (APPROVED)
        res_file1 = next(r for r in results if r["file_id"] == "FID-00001")
        self.assertEqual(res_file1["status"], "APPROVED")
        
        # File 2: Status harus tinjauan operator (PENDING_REVIEW)
        res_file2 = next(r for r in results if r["file_id"] == "FID-00002")
        self.assertEqual(res_file2["status"], "PENDING_REVIEW")
        self.assertEqual(res_file2["target_folder_suggestion"], "90_NEEDS_REVIEW/11_FINGERPRINT_NO_MATCH")

    def test_operation_log_and_rollback_safety(self):
        """Menguji manajer log operasi dan manajer pemulihan (rollback) serta pagar pengaman."""
        # 1. Catat log operasi baru
        op_id = log_operation(
            logs_dir=self.logs_dir,
            file_id="FID-00099",
            operation_type="COPY_RENAME_TAG",
            source_path=self.dummy_source1,
            target_path=self.dummy_dest,
            old_filename="dummy_source1.mp3",
            new_filename="dummy_dest.mp3",
            old_tags={"artist_tag": "Artis Lama", "title_tag": "Judul Lama"},
            new_tags={"artist_tag": "Artis Baru", "title_tag": "Judul Baru"},
            decision_source="OPERATOR_APPROVED",
            confidence_score=100.0,
            operator="OPERATOR"
        )
        self.assertIsNotNone(op_id)
        
        # Simulasikan penyalinan berkas fisik di disk untuk rollback test
        shutil.copy2(self.dummy_source1, self.dummy_dest)
        self.assertTrue(os.path.exists(self.dummy_dest))
        
        # 2. Catat manifest pemulihan rollback
        ok = write_to_rollback_manifest(
            logs_dir=self.logs_dir,
            operation_id=op_id,
            file_id="FID-00099",
            current_path=self.dummy_dest,
            original_source_path=self.dummy_source1,
            original_filename="dummy_source1.mp3",
            original_tags={"artist_tag": "Artis Lama", "title_tag": "Judul Lama", "genre_tag": "Pop"}
        )
        self.assertTrue(ok)
        
        # 3. Uji pagar pengaman rollback (tidak boleh memodifikasi berkas di folder input stasiun radio)
        # Kita manipulasi manifest agar target pemulihan mengarah ke data/input
        bad_manifest_path = os.path.join(self.logs_dir, "rollback_manifest.csv")
        self.assertTrue(os.path.exists(bad_manifest_path))
        
        # Simulasikan modifikasi manifest ilegal ke path input
        rows = []
        with open(bad_manifest_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                # Masukkan kata "data/input" secara paksa
                r["current_path"] = os.path.join("data", "input", "dummy_dest.mp3")
                rows.append(r)
                
        with open(bad_manifest_path, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=reader.fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            
        # Eksekusi rollback ilegal
        success, msg = execute_rollback_for_file(logs_dir=self.logs_dir, operation_id=op_id)
        self.assertFalse(success)
        self.assertIn("pagar pengaman", msg.lower())
        
        # 4. Kembalikan manifest ke yang legal dan eksekusi rollback sukses
        rows = []
        with open(bad_manifest_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                r["current_path"] = self.dummy_dest
                rows.append(r)
                
        with open(bad_manifest_path, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=reader.fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            
        # Pindahkan dummy_source1 kembali agar rename aman tidak crash
        if os.path.exists(self.dummy_source1):
            os.remove(self.dummy_source1)
            
        # Eksekusi rollback legal
        with patch("src.rollback_manager.write_basic_metadata") as mock_write:
            mock_write.return_value = ("SUCCESS", "Mock write tag ok")
            success, msg = execute_rollback_for_file(logs_dir=self.logs_dir, operation_id=op_id)
            self.assertTrue(success)
            self.assertTrue(os.path.exists(self.dummy_source1))
            self.assertFalse(os.path.exists(self.dummy_dest))


if __name__ == "__main__":
    unittest.main()
