# IT Helpdesk Inventory Collector Integration

Integrasi script Python untuk pengumpulan spesifikasi PC otomatis pada sistem IT Helpdesk berbasis CodeIgniter 4.

## 📋 Overview

Sistem ini memungkinkan user untuk secara otomatis mengumpulkan spesifikasi PC mereka melalui script Python dan mengirimkannya ke server IT Helpdesk untuk memperbarui inventory.

### Flow Sistem:

1. User melakukan registrasi → akun dibuat + record inventory kosong
2. User download script Python dari dashboard
3. User jalankan script → otomatis collect data PC → kirim ke API CI4
4. Server update inventory berdasarkan email user

## 🛠️ Technical Requirements

### Python Script:

- **Python Version**: 3.6+
- **OS Support**: Windows 7/8/10/11
- **Dependencies**: psutil, requests

### CI4 Backend:

- **Framework**: CodeIgniter 4
- **Database**: MySQL/MariaDB
- **API**: RESTful dengan ResponseTrait

## 📁 File Structure

```
project-root/
├── inventory_collector.py      # Script Python utama
├── requirements.txt            # Dependencies Python
├── README.md                   # Dokumentasi ini
└── app/
    ├── Controllers/
    │   └── Api.php            # API endpoint update-main-device
    ├── Config/
    │   └── Routes.php         # Route API
    └── Views/
        └── v_download_script.php # Halaman download script
```

## 🚀 Setup & Installation

### 1. Python Environment Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Atau install manual
pip install psutil>=5.8.0 requests>=2.25.1
# Windows only:
pip install wmi>=1.5.1
```

### 2. CI4 Configuration

#### Routes (app/Config/Routes.php)

```php
$routes->group('api', function ($routes) {
    // ... existing routes ...
    $routes->post('update-main-device', 'Api::updateMainDevice');
});
```

#### API Controller (app/Controllers/Api.php)

Method `updateMainDevice()` sudah ditambahkan dengan:

- Validasi email dan data
- Rate limiting (10 request/user/jam)
- Update/Create maindevice record
- Logging perubahan

### 3. Database Structure

Sistem menggunakan tabel existing:

- `users` (email_users, nama_users)
- `karyawan` (nama_karyawan, departemen_karyawan)
- `inventory` (karyawan_id, main_id, support_id)
- `maindevice` (manufaktur, cpu, ram, os, dll.)
- `log` (logging perubahan)

## 📊 Data yang Dikumpulkan

Script Python mengumpulkan spesifikasi berikut:

| Field      | Description      | Source                  |
| ---------- | ---------------- | ----------------------- |
| manufaktur | Manufacturer PC  | Manual input by admin   |
| cpu        | CPU Information  | psutil.cpu_info()       |
| ram        | RAM Capacity     | psutil.virtual_memory() |
| os         | Operating System | platform.platform()     |
| ipaddress  | IP Address       | socket.gethostbyname()  |
| hostname   | Hostname         | platform.node()         |
| storage    | Total Storage    | psutil.disk_usage()     |

**Note**: Field `jenis`, `lisensi_windows`, `credential`, `office`, `lisensi_office` diset NULL dan diisi manual oleh admin.

## 🔗 API Endpoint

### POST /api/update-main-device

**Request Body:**

```json
{
  "email": "user@example.com",
  "data": {
    "manufaktur": "Windows",
    "cpu": "Intel Core i5",
    "ram": "16.0 GB",
    "os": "Windows-10-10.0.19041-SP0",
    "ipaddress": "192.168.1.100",
    "hostname": "DESKTOP-ABC123",
    "storage": "500.0 GB",
    "jenis": null,
    "lisensi_windows": null,
    "credential": null,
    "office": null,
    "lisensi_office": null
  }
}
```

**Response Success:**

```json
{
  "status": "success",
  "message": "Main device data updated successfully",
  "main_id": 123
}
```

**Response Error:**

```json
{
  "status": "error",
  "message": "User not found"
}
```

## 🎯 Usage Guide

### Untuk User:

1. **Registrasi**: Daftar akun di sistem IT Helpdesk
2. **Download Script**: Akses menu "Download Script" di sidebar
3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Jalankan Script**:
   ```bash
   python inventory_collector.py
   ```
5. **Input Email**: Masukkan email yang didaftarkan
6. **Konfirmasi**: Script akan menampilkan data yang dikumpul, konfirmasi sebelum kirim
7. **Selesai**: Data terkirim ke server, inventory terupdate

### Untuk Admin:

- Monitor log perubahan di tabel `log`
- Lengkapi data manual (jenis device, lisensi, dll.) melalui admin panel
- Manage inventory melalui interface existing

## 🔒 Security & Rate Limiting

- **Rate Limiting**: 10 request per user per jam
- **Email Validation**: Validasi format email dan existence di database
- **Data Validation**: Validasi struktur data yang dikirim
- **Logging**: Semua perubahan dicatat di tabel log

## 🐛 Troubleshooting

### Script Python Tidak Berjalan:

- Pastikan Python 3.6+ terinstall
- Install dependencies: `pip install -r requirements.txt`

### Error "User not found":

- Pastikan email yang diinput sudah terdaftar di sistem
- Periksa koneksi internet

### Error "Rate limit exceeded":

- Tunggu 1 jam sebelum mencoba lagi
- Atau hubungi admin untuk reset limit

### Data Tidak Update di Dashboard:

- Refresh halaman dashboard
- Pastikan script berhasil mengirim data (lihat pesan sukses)
- Hubungi admin jika masalah berlanjut

## 📝 Development Notes

### Menambah Field Baru:

1. Update migration `maindevice` table
2. Update script Python untuk collect data baru
3. Update API controller untuk handle field baru
4. Update dokumentasi

### Testing:

```bash
# Test API endpoint
curl -X POST http://localhost/api/update-main-device \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","data":{...}}'

# Test Python script
python inventory_collector.py
```

## 🤝 Contributing

Untuk pengembangan lebih lanjut:

- Tambahkan error handling yang lebih robust
- Support untuk OS lain (Linux, macOS)
- GUI interface untuk script Python
- Batch processing untuk multiple devices

## 📞 Support

Untuk bantuan atau pertanyaan:

- Buat issue di repository GitHub
- Hubungi tim IT Helpdesk
- Dokumentasi lengkap tersedia di wiki project

---

**Version**: 1.0.0
**Last Updated**: 2025-01-15
**Compatible**: Windows 7/8/10/11, Python 3.6+
