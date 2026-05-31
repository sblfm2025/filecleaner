# 09 — CLI dan Mode Aman

## 1. Prinsip CLI

Tool harus bisa dijalankan dari terminal:

```bash
python run.py --scan
python run.py --preview
python run.py --apply-rename
python run.py --write-tags
python run.py --sort
python run.py --duplicates
python run.py --validate
```

## 2. Default Harus Aman

Jika user menjalankan:

```bash
python run.py
```

Maka sistem hanya menampilkan bantuan dan tidak mengubah file.

Jika user menjalankan pipeline:

```bash
python scripts/99_full_pipeline.py
```

Default tetap:

```text
DRY_RUN = True
APPLY_RENAME = False
WRITE_METADATA = False
SORT_FILES = False
```

## 3. Mode Aman

### Scan

```bash
python run.py --scan
```

Hanya membaca file dan membuat laporan.

### Preview

```bash
python run.py --preview
```

Hanya membuat usulan nama file baru.

### All Safe

```bash
python run.py --all-safe
```

Menjalankan:

```text
scan
preview
duplicate check ringan
summary
```

Tidak rename, tidak tulis metadata, tidak sortir final.

## 4. Mode Apply

Untuk benar-benar menyalin dan rename:

```bash
python run.py --apply-rename
```

Untuk metadata:

```bash
python run.py --write-tags
```

Untuk sortir:

```bash
python run.py --sort
```

Untuk pipeline apply eksplisit:

```bash
python run.py --apply-rename --write-tags --sort
```

## 5. Konfirmasi Apply

Saat mode apply dijalankan, tampilkan peringatan:

```text
Anda akan membuat salinan hasil proses ke folder output.
File asli tidak akan diubah.
Lanjutkan? ketik YES untuk lanjut:
```

Tanpa `YES`, proses batal.

## 6. Resume

Flag:

```bash
python run.py --resume
```

Sistem membaca:

```text
data/logs/process_manifest.csv
```

Lalu skip file yang sudah selesai.

## 7. Batch ID

Flag:

```bash
python run.py --scan --batch-id BATCH_20260531_001
```

Jika batch_id tidak diberikan, sistem membuat otomatis.

## 8. Contoh Alur Operator

```bash
python run.py --scan --batch-id BATCH_001
python run.py --preview --batch-id BATCH_001
python run.py --apply-rename --batch-id BATCH_001
python run.py --write-tags --batch-id BATCH_001
python run.py --sort --batch-id BATCH_001
python run.py --duplicates --batch-id BATCH_001
python run.py --validate --batch-id BATCH_001
```

## 9. Exit Code

Gunakan exit code:

```text
0 = sukses
1 = error umum
2 = config error
3 = input folder kosong
4 = apply dibatalkan user
5 = permission/path error
```

## 10. Output Terminal

Tampilkan progres ringkas:

```text
[SCAN] 120/5000 files processed
[PREVIEW] 120/5000 files processed
[RENAME] copied: 100, needs_review: 20
[METADATA] written: 80, skipped: 40
[SORT] output: 95, review: 25
```

Jangan spam terlalu banyak. Detail masuk ke log.
