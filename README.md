# Finance Manager

Finance Manager adalah aplikasi web untuk mengelola keuangan pribadi Anda. Aplikasi ini memungkinkan Anda untuk mencatat transaksi, mengelola tagihan, anggaran, dan hutang/piutang, serta menghasilkan laporan dalam format PDF dan Excel.

## Fitur

- **Tambah Transaksi**: Catat pemasukan dan pengeluaran Anda.
- **Lihat Transaksi**: Lihat semua transaksi yang telah dicatat.
- **Hitung Saldo**: Hitung saldo berdasarkan pemasukan dan pengeluaran.
- **Tambah Tagihan**: Tambahkan tagihan rutin yang perlu dibayar.
- **Lihat Tagihan**: Lihat semua tagihan yang telah dicatat.
- **Tambah Anggaran**: Tambahkan anggaran bulanan untuk kategori tertentu.
- **Lihat Anggaran**: Lihat semua anggaran yang telah dicatat.
- **Tambah Hutang/Piutang**: Catat hutang dan piutang Anda.
- **Lihat Hutang/Piutang**: Lihat semua hutang dan piutang yang telah dicatat.
- **Download Laporan PDF**: Unduh laporan transaksi dalam format PDF.
- **Download Laporan Excel**: Unduh laporan transaksi dalam format Excel.

## Instalasi

1. Clone repositori ini:
    ```bash
    git clone https://github.com/username/finance_manager.git
    cd finance_manager
    ```

2. Buat virtual environment dan aktifkan:
    ```bash
    python -m venv venv
    venv\Scripts\activate  # Untuk Windows
    source venv/bin/activate  # Untuk macOS/Linux
    ```

3. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4. Konfigurasi database MySQL:
    - Buat database `finance_manager`.
    - Sesuaikan konfigurasi database di file [app.py](http://_vscodecontentref_/0) pada fungsi [connect_to_database()](http://_vscodecontentref_/1).

5. Jalankan aplikasi:
    ```bash
    python app.py
    ```

6. Buka browser dan akses `http://127.0.0.1:5000`.
