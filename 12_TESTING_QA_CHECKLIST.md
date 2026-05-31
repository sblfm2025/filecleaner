# 12 — Testing dan QA Checklist

## 1. Uji Struktur Project

- [ ] Semua folder project dibuat.
- [ ] `requirements.txt` tersedia.
- [ ] `config/*.json` tersedia.
- [ ] `scripts/*.py` tersedia.
- [ ] `src/*.py` tersedia.
- [ ] `docs/*.md` tersedia.

## 2. Uji Install

- [ ] Python terdeteksi.
- [ ] `pip install -r requirements.txt` berhasil.
- [ ] Tidak ada dependency berbayar.
- [ ] Tidak butuh login online.

## 3. Uji Scan

Gunakan 20–50 file.

- [ ] File audio terdeteksi.
- [ ] File non-audio diabaikan/dicatat.
- [ ] Metadata terbaca.
- [ ] Durasi terbaca.
- [ ] CSV dibuat.
- [ ] XLSX dibuat.
- [ ] File corrupt tidak menghentikan proses.

## 4. Uji Preview Rename

- [ ] Nama kotor dibersihkan.
- [ ] `Official Video` dihapus.
- [ ] `Lyrics/Lirik` dihapus.
- [ ] `320kbps` dihapus.
- [ ] Underscore menjadi spasi.
- [ ] Format `Artis - Judul` dipertahankan.
- [ ] Versi penting seperti `(Acoustic)` tidak dihapus.
- [ ] Tidak ada file fisik berubah.

## 5. Uji Apply Rename

- [ ] File sumber tidak berubah.
- [ ] File disalin ke output.
- [ ] Nama hasil sesuai preview.
- [ ] Nama bentrok diberi angka.
- [ ] Tidak ada overwrite.
- [ ] Log dibuat.

## 6. Uji Metadata

- [ ] Title kosong diisi dari filename.
- [ ] Artist kosong diisi dari filename.
- [ ] Tag yang sudah ada tidak ditimpa.
- [ ] Album default diisi jika kosong.
- [ ] Genre default diisi jika kosong.
- [ ] File ambigu dilewati.
- [ ] Error metadata dicatat.

## 7. Uji Sortir

- [ ] JINGLE masuk folder jingle.
- [ ] BUMPER masuk folder bumper.
- [ ] IKLAN masuk folder iklan.
- [ ] ILM masuk folder layanan publik.
- [ ] Bugis/Makassar/Mandar masuk folder lokal.
- [ ] Dangdut masuk folder dangdut.
- [ ] File ragu masuk PERLU_DICEK.
- [ ] Output struktur lengkap.

## 8. Uji Duplikat

- [ ] Nama sama terdeteksi.
- [ ] Durasi mirip terdeteksi.
- [ ] Tag sama terdeteksi.
- [ ] Tidak ada file dihapus.
- [ ] Laporan duplikat dibuat.

## 9. Uji Batch

- [ ] Batch ID dibuat.
- [ ] Log per batch dibuat.
- [ ] Proses bisa dihentikan.
- [ ] Resume berhasil.
- [ ] File selesai tidak diproses ulang.
- [ ] Manifest terisi.

## 10. Uji Ratusan GB Bertahap

Tahapan:

```text
20–50 file
5 GB
10 GB
30–50 GB
100 GB
```

Checklist:

- [ ] RAM stabil.
- [ ] Proses tidak crash.
- [ ] Log tetap ditulis.
- [ ] Output tidak overwrite.
- [ ] Resume bekerja.
- [ ] Waktu proses masih masuk akal.

## 11. Uji Keamanan

- [ ] Tidak ada fungsi delete otomatis.
- [ ] Tidak ada move dari sumber asli.
- [ ] Tidak ada overwrite.
- [ ] Apply butuh konfirmasi.
- [ ] Default dry-run.
- [ ] File asli tetap sama.

## 12. Kriteria Siap Dipakai

Sistem boleh dipakai untuk batch besar jika:

- [ ] Uji 50 file aman.
- [ ] Uji 5 GB aman.
- [ ] Uji 50 GB aman.
- [ ] Hasil rename masuk akal.
- [ ] Metadata tidak kacau.
- [ ] PERLU_DICEK berfungsi.
- [ ] Operator paham alurnya.
