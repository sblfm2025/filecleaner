import os
import csv
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

class BatchManager:
    """
    Mengelola pencatatan status pemrosesan file audio ke dalam process_manifest.csv.
    Mendukung fitur resume dengan membaca status sebelumnya dan melakukan checkpointing.
    """
    
    COLUMNS = [
        "batch_id", "file_id", "source_path", "source_size", "source_modified_time",
        "current_stage", "scan_status", "rename_status", "metadata_status", 
        "sort_status", "duplicate_status", "target_path", "error_message", "processed_at"
    ]
    
    def __init__(self, logs_dir: str = "data/logs"):
        self.logs_dir = logs_dir
        self.manifest_path = os.path.join(logs_dir, "process_manifest.csv")
        self.manifest_data: Dict[str, Dict[str, Any]] = {}
        
        os.makedirs(self.logs_dir, exist_ok=True)
        self._load_manifest()

    def _load_manifest(self) -> None:
        """Memuat data manifest dari CSV jika sudah ada."""
        if not os.path.exists(self.manifest_path):
            self._write_header()
            return
            
        try:
            with open(self.manifest_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Bersihkan jika ada kolom kosong/tidak sesuai
                    source_path = row.get("source_path")
                    if source_path:
                        self.manifest_data[source_path] = row
        except Exception as e:
            logging.error(f"Gagal membaca process_manifest.csv: {e}. Membuat ulang manifes kosong di RAM.")

    def _write_header(self) -> None:
        """Menulis header manifest ke berkas CSV."""
        try:
            with open(self.manifest_path, mode='w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(self.COLUMNS)
        except Exception as e:
            logging.error(f"Gagal menulis header process_manifest.csv: {e}")

    def save_all_to_csv(self) -> None:
        """Menyimpan seluruh data manifes dari RAM ke berkas CSV."""
        try:
            # Tulis ke file temporer lalu rename untuk mencegah korupsi data jika terhenti tengah jalan
            temp_path = self.manifest_path + ".tmp"
            with open(temp_path, mode='w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self.COLUMNS)
                writer.writeheader()
                for row in self.manifest_data.values():
                    # Pastikan row hanya berisi kolom yang valid
                    clean_row = {col: row.get(col, "") for col in self.COLUMNS}
                    writer.writerow(clean_row)
                    
            if os.path.exists(self.manifest_path):
                os.remove(self.manifest_path)
            os.rename(temp_path, self.manifest_path)
        except Exception as e:
            logging.error(f"Gagal menyimpan process_manifest.csv: {e}")

    def get_file_record(self, source_path: str) -> Optional[Dict[str, Any]]:
        """Mendapatkan data rekam proses untuk path file tertentu."""
        return self.manifest_data.get(source_path)

    def register_file(self, source_path: str, batch_id: str, file_size: float, modified_time: str) -> Dict[str, Any]:
        """
        Mendaftarkan file baru ke manifest jika belum ada.
        Jika sudah ada, mengembalikan record yang lama.
        """
        if source_path in self.manifest_data:
            record = self.manifest_data[source_path]
            # Jika didaftarkan dengan batch baru, perbarui batch_id dan reset status pemrosesan
            if record.get("batch_id") != batch_id:
                record["batch_id"] = batch_id
                record["current_stage"] = "PENDING"
                record["scan_status"] = "PENDING"
                record["rename_status"] = "PENDING"
                record["metadata_status"] = "PENDING"
                record["sort_status"] = "PENDING"
                record["duplicate_status"] = "PENDING"
                record["target_path"] = ""
                record["error_message"] = ""
                record["processed_at"] = ""
                self.manifest_data[source_path] = record
                self.save_all_to_csv()
            return record
            
        file_id = f"F_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(self.manifest_data) + 1:05d}"
        
        record = {
            "batch_id": batch_id,
            "file_id": file_id,
            "source_path": source_path,
            "source_size": f"{file_size:.4f}",
            "source_modified_time": modified_time,
            "current_stage": "PENDING",
            "scan_status": "PENDING",
            "rename_status": "PENDING",
            "metadata_status": "PENDING",
            "sort_status": "PENDING",
            "duplicate_status": "PENDING",
            "target_path": "",
            "error_message": "",
            "processed_at": ""
        }
        
        self.manifest_data[source_path] = record
        self.save_all_to_csv()
        return record

    def update_file_status(self, source_path: str, stage: str, status: str, error_msg: str = "", target_path: str = "") -> None:
        """
        Memperbarui status pengerjaan file untuk tahapan tertentu.
        Tahapan (stage): scan, rename, metadata, sort, duplicate
        """
        if source_path not in self.manifest_data:
            logging.warning(f"Mencoba memperbarui status file yang belum terdaftar: {source_path}")
            return
            
        record = self.manifest_data[source_path]
        record["current_stage"] = stage.upper()
        
        if stage == "scan":
            record["scan_status"] = status
        elif stage == "rename":
            record["rename_status"] = status
        elif stage == "metadata":
            record["metadata_status"] = status
        elif stage == "sort":
            record["sort_status"] = status
        elif stage == "duplicate":
            record["duplicate_status"] = status
            
        if error_msg:
            record["error_message"] = error_msg
            
        if target_path:
            record["target_path"] = target_path
            
        record["processed_at"] = datetime.now().isoformat()
        
        self.manifest_data[source_path] = record
        self.save_all_to_csv() # Checkpoint langsung ke disk

    def get_pending_files(self, batch_id: str, stage: str) -> List[Dict[str, Any]]:
        """Mendapatkan daftar file yang belum selesai diproses untuk tahapan tertentu."""
        pending = []
        status_field = f"{stage.lower()}_status"
        
        for record in self.manifest_data.values():
            if record.get("batch_id") == batch_id:
                if record.get(status_field, "PENDING") in ["PENDING", "ERROR", "FAILED"]:
                    pending.append(record)
        return pending

    def get_all_records_for_batch(self, batch_id: str) -> List[Dict[str, Any]]:
        """Mengambil semua rekam proses untuk ID batch tertentu. Fallback ke batch terakhir jika batch_id kosong/tidak ditemukan."""
        records = [row for row in self.manifest_data.values() if row.get("batch_id") == batch_id]
        if not records and self.manifest_data:
            # Ambil semua batch_id unik
            batch_ids = list(set(row.get("batch_id", "") for row in self.manifest_data.values() if row.get("batch_id")))
            if batch_ids:
                # Urutkan secara alfabetis (karena format BATCH_YYYYMMDD_HHMMSS cocok diurutkan alfabetis)
                latest_batch_id = sorted(batch_ids)[-1]
                records = [row for row in self.manifest_data.values() if row.get("batch_id") == latest_batch_id]
                logging.info(f"ID Batch '{batch_id}' kosong di manifest. Menggunakan data dari batch terbaru: '{latest_batch_id}'")
        return records
