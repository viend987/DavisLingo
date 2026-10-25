# DavisLingo

<p align="center">
  <img src="app.png" alt="DavisLingo Logo" width="128" height="128">
</p>

<p align="center">
  <strong>Fast, Authentic, In-Game Roleplay English Assistant for GTA V (FiveM / JGVRP)</strong><br>
  Developed by <strong>Viend (ViendLab)</strong> • Made by JGVRP Player for GTA V Roleplay
</p>

<p align="center">
  <a href="https://github.com/viend987/DavisLingo/releases/latest"><img src="https://img.shields.io/github/v/release/viend987/DavisLingo?style=flat-square&color=0284c7" alt="Latest Release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-emerald.svg?style=flat-square" alt="License"></a>
  <a href="https://davislingo.viend.my.id"><img src="https://img.shields.io/badge/Website-davislingo.viend.my.id-blue.svg?style=flat-square" alt="Website"></a>
</p>

---

## 📖 Overview

**DavisLingo** adalah aplikasi desktop berbasis Python dan CustomTkinter yang dirancang khusus untuk pemain GTA V Roleplay (FiveM / JGVRP) di Indonesia. Aplikasi ini membantu pemain berkomunikasi dalam bahasa Inggris secara fasih, otentik, dan sesuai faksi atau gaya peran (persona) tanpa membuat alur roleplay menjadi kaku atau lambat.

Dilengkapi dengan **HUD Overlay tembus pandang (semi-transparent)** di atas layar game, OCR realtime berakurasi tinggi, serta sistem makro instan satu tombol untuk membalas chat lawan bicara.

---

## ✨ Fitur Utama

- **6 Persona Faksi Roleplay**:
  - 🚒 **LSFD / Fire & Medic**: Doktrin paramedis & damkar Los Santos (referensi doktrin JGVRP), taktis di radio (*Status-2, Status-6, 10-4, CAT-A/B*), serta penanganan medis klinis (*BLS/ILS*) yang tenang dan empatik.
  - 🚓 **LSPD / Police & Sheriff**: Prosedural, taktis, tegas, dan otoriter dalam penertiban situasi maupun transmisi radio patroli.
  - 🏙️ **LA Street Gang**: Dialek jalanan otentik West Coast / South Central (AAVE) yang *gritty* dan natural.
  - 👥 **Casual Civilian**: Percakapan bahasa Inggris natural warga kota harian.
  - 🌵 **Cartel & Latino**: Gaya bicara narco bilingual dengan istilah khas (*hermano, jefe, tranquilo, compa*).
  - 🍸 **Mafia Underworld**: Sindikat terorganisir yang sopan, dingin, berwibawa, dan intimidatif.

- **5 Emosi / Nada Bicara (Tone)**: *Neutral*, *Calm & Assertive*, *Friendly & Empathetic*, *Angry & Intimidating*, dan *Panic & Urgent*.

- **HUD Overlay Game Modern**:
  - Desain minimalis obsidian / slate tanpa tombol kurung siku yang mengganggu.
  - Dapat diatur transparansinya (*opacity*), posisi, dan ukurannya langsung di layar.
  - Menampilkan hasil terjemahan chat lawan bicara beserta 3 opsi jawaban bahasa Inggris yang dilengkapi panduan maksud (*intent/vibe*) dalam bahasa Indonesia.

- **Optimasi OCR Tesseract**:
  - *Preprocessing* cerdas: *Lanczos 2x upsampling*, penyesuaian kontras (1.8x), dan *sharpness* (1.6x) untuk mengenali font chat FiveM bergradasi warna.
  - Pembersihan otomatis cap waktu `[hh:mm:ss]` dan *noise* sebelum diproses oleh AI.

- **Mesin Penerjemah Cepat (LPU Accelerated)**:
  - Didukung oleh model AI generasi terbaru via **Groq LPU API** dengan latensi milidetik, sehingga Anda tidak tertinggal tempo saat percakapan RP berlangsung cepat.

- **Sistem Pembaruan Otomatis (In-App Auto-Updater)**:
  - Otomatis memeriksa rilis terbaru langsung dari **GitHub Releases** dengan *fallback* ke Cloudflare Edge Worker.
  - Pengaturan pribadi (`config.json`), API Key, dan koordinat scan layar Anda terlindungi dan tidak akan tertimpa saat update.

---

## ⌨️ Shortcut / Keybind Default

| Aksi | Shortcut Default | Keterangan |
| :--- | :--- | :--- |
| **Scan Layar (OCR)** | `F4` | Memindai area chat game dan menampilkan 3 opsi jawaban di HUD |
| **Auto-Replace Ketikan** | `F5` | Mengganti teks chat yang diblock langsung dengan terjemahan bahasa Inggris RP |
| **Kirim Opsi 1** | `Ctrl + 1` | Memilih & menyalin opsi balasan 1 |
| **Kirim Opsi 2** | `Ctrl + 2` | Memilih & menyalin opsi balasan 2 |
| **Kirim Opsi 3** | `Ctrl + 3` | Memilih & menyalin opsi balasan 3 |
| **Ganti Persona** | `Alt + 1` | Berpindah faksi/persona secara berurutan |
| **Ganti Tone** | `Alt + 3` | Mengubah nada emosi (Santai, Tegas, dll) |
| **Sembunyikan HUD** | `Insert` | *Toggle* tampilan HUD Overlay on/off |

*Semua tombol shortcut di atas dapat dikustomisasi secara bebas melalui tab **Custom Keybinds** di aplikasi.*

---

## 🚀 Cara Menjalankan

### Opsi A: Versi Portable Siap Pakai (Rekomendasi)
1. Unduh arsip zip versi terbaru dari halaman [Releases](https://github.com/viend987/DavisLingo/releases).
2. Ekstrak file zip ke folder mana saja di komputer Anda.
3. Jalankan `Start_DavisLingo.bat` atau `DavisLingo.exe`.
4. Masukkan **Groq API Key** Anda pada tab **Roleplay & HUD** (dapat dibuat gratis di [console.groq.com](https://console.groq.com)).

### Opsi B: Menjalankan dari Source Code (Python)
1. Pastikan Anda telah menginstal **Python 3.12+** dan **Git**.
2. Clone repository ini:
   ```bash
   git clone https://github.com/viend987/DavisLingo.git
   cd DavisLingo
   ```
3. Install dependensi yang dibutuhkan:
   ```bash
   pip install customtkinter pillow requests keyboard pyperclip pyreadline3
   ```
4. Salin file template konfigurasi:
   ```bash
   copy config.example.json config.json
   ```
5. Jalankan aplikasi:
   ```bash
   python main.py
   ```

---

## 🛠️ Kompilasi ke Executable (PyInstaller)

Jika ingin mem-build binary standalone sendiri:
```bash
pyinstaller DavisLingo.spec --noconfirm
```
File executable dan bundle dependensi akan tersimpan di dalam folder `dist/DavisLingo/`.

---

## 📄 Lisensi

Didistribusikan di bawah Lisensi **MIT**. Lihat berkas [LICENSE](LICENSE) untuk informasi lebih lanjut.

---

<p align="center">
  Dibuat dengan ❤️ untuk komunitas GTA V Roleplay Indonesia oleh <strong>ViendLab</strong>.
</p>
