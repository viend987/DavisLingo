import os
import sys
import re
import json
import time
import tempfile
import subprocess
import requests

CURRENT_VERSION = "3.2.1"
GITHUB_REPO = "viend987/DavisLingo"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
FALLBACK_API_URL = "https://davislingo.viend.my.id/api/version"

def get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def parse_version_tuple(v_str):
    nums = re.findall(r"\d+", str(v_str))
    return tuple(int(x) for x in nums) if nums else (0, 0, 0)

class UpdaterService:
    def __init__(self, log_callback=None):
        self.log = log_callback or print
        self.current_version = CURRENT_VERSION
        self.base_dir = get_base_dir()

    def check_for_updates(self, timeout=6):
        """
        Check if a newer version is available.
        Checks GitHub Releases API first, with fallback to edge worker.
        Returns: (has_update: bool, update_info: dict)
        """
        # 1. Try GitHub Releases API
        try:
            gh_headers = {
                "User-Agent": f"DavisLingo-Desktop/{self.current_version}",
                "Accept": "application/vnd.github.v3+json"
            }
            res = requests.get(GITHUB_API_URL, headers=gh_headers, timeout=timeout)
            if res.status_code == 200:
                data = res.json()
                tag = data.get("tag_name", "").lstrip("v").strip()
                if tag:
                    latest_v = tag
                    cur_tuple = parse_version_tuple(self.current_version)
                    lat_tuple = parse_version_tuple(latest_v)
                    has_update = lat_tuple > cur_tuple

                    # Find download url from release assets
                    download_url = f"https://github.com/{GITHUB_REPO}/releases/latest/download/DavisLingo_Portable.zip"
                    assets = data.get("assets", [])
                    for a in assets:
                        aname = a.get("name", "").lower()
                        if aname.endswith(".zip") and "portable" in aname:
                            download_url = a.get("browser_download_url", download_url)
                            break
                        elif aname.endswith(".zip"):
                            download_url = a.get("browser_download_url", download_url)

                    info = {
                        "has_update": has_update,
                        "current_version": self.current_version,
                        "latest_version": latest_v,
                        "release_date": str(data.get("published_at", "-"))[:10],
                        "changelog": data.get("body", "Pembaruan rilis GitHub."),
                        "download_url": download_url,
                        "mandatory": False
                    }
                    return has_update, info
        except Exception as gh_e:
            self.log(f"[UPDATER] GitHub check: {gh_e}. Menggunakan fallback edge server...")

        # 2. Fallback to Edge Server API
        try:
            headers = {"User-Agent": f"DavisLingo-Desktop/{self.current_version}"}
            res = requests.get(FALLBACK_API_URL, headers=headers, timeout=timeout)
            if res.status_code == 200:
                data = res.json()
                latest_v = data.get("latest_version", self.current_version)
                cur_tuple = parse_version_tuple(self.current_version)
                lat_tuple = parse_version_tuple(latest_v)
                has_update = lat_tuple > cur_tuple
                info = {
                    "has_update": has_update,
                    "current_version": self.current_version,
                    "latest_version": latest_v,
                    "release_date": data.get("release_date", "-"),
                    "changelog": data.get("changelog", "Pembaruan sistem."),
                    "download_url": data.get("download_url", f"https://github.com/{GITHUB_REPO}/releases/latest/download/DavisLingo_Portable.zip"),
                    "mandatory": data.get("mandatory", False)
                }
                return has_update, info
            else:
                self.log(f"[UPDATER] Server returned code {res.status_code}")
                return False, {}
        except Exception as e:
            self.log(f"[UPDATER] Gagal cek versi: {e}")
            return False, {}

    def download_update_package(self, download_url, dest_zip_path, progress_callback=None):
        """
        Download zip file with automatic Google Drive confirmation bypass and progress streaming.
        progress_callback: fn(percent_float, downloaded_mb, total_mb)
        """
        session = requests.Session()
        session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) DavisLingoUpdater"})

        # Request initial URL (follows 302 redirects)
        res = session.get(download_url, stream=True, timeout=15)
        if res.status_code != 200:
            raise RuntimeError(f"Gagal mengunduh: HTTP {res.status_code}")

        # Check if Google Drive returned virus warning confirmation page
        content_type = res.headers.get("Content-Type", "")
        if "text/html" in content_type:
            html = res.text
            uuid_match = re.search(r'name=["\']uuid["\']\s+value=["\']([^"\']+)["\']', html)
            id_match = re.search(r'name=["\']id["\']\s+value=["\']([^"\']+)["\']', html)
            
            if uuid_match:
                uuid_val = uuid_match.group(1)
                file_id = id_match.group(1) if id_match else "1F3TUcltW0bQSe8VfwFkQpmu8d44Bbbci"
                confirm_url = f"https://drive.usercontent.google.com/download?id={file_id}&export=download&authuser=0&confirm=t&uuid={uuid_val}"
                res = session.get(confirm_url, stream=True, timeout=20)
                if res.status_code != 200:
                    raise RuntimeError(f"Gagal bypass konfirmasi Google Drive: HTTP {res.status_code}")

        total_size = int(res.headers.get("Content-Length", 0))
        downloaded = 0
        chunk_size = 64 * 1024 # 64 KB

        with open(dest_zip_path, "wb") as f:
            for chunk in res.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback:
                        percent = (downloaded / total_size * 100) if total_size > 0 else 0
                        dl_mb = downloaded / (1024 * 1024)
                        tot_mb = total_size / (1024 * 1024)
                        progress_callback(percent, dl_mb, tot_mb)

        # Validate that downloaded file is a valid ZIP
        if os.path.exists(dest_zip_path) and os.path.getsize(dest_zip_path) > 1024:
            with open(dest_zip_path, "rb") as check_f:
                magic = check_f.read(4)
                if not magic.startswith(b"PK\x03\x04"):
                    raise RuntimeError("File hasil unduhan bukan arsip ZIP yang valid.")
            return True
        else:
            raise RuntimeError("Ukuran file unduhan tidak valid atau kosong.")

    def launch_updater_and_restart(self, zip_path):
        """
        Generate updater script and launch it, then close current DavisLingo instance.
        """
        temp_dir = tempfile.gettempdir()
        runner_bat = os.path.join(temp_dir, "davislingo_update_runner.bat")
        app_dir = self.base_dir
        cur_pid = os.getpid()

        bat_content = f"""@echo off
chcp 65001 >nul
title DavisLingo Auto-Updater
color 0B
cls
echo ===================================================================
echo             DavisLingo Auto-Updater ^| by ViendLab
echo ===================================================================
echo.
echo [1/4] Menunggu proses DavisLingo selesai (PID: {cur_pid})...
timeout /t 2 /nobreak >nul

taskkill /F /PID {cur_pid} >nul 2>&1
taskkill /F /IM DavisLingo.exe >nul 2>&1
timeout /t 1 /nobreak >nul

echo [2/4] Mengekstrak paket pembaruan...
set "EXTRACT_DIR=%TEMP%\\davislingo_extracted"
if exist "%EXTRACT_DIR%" rd /s /q "%EXTRACT_DIR%"
md "%EXTRACT_DIR%"

tar -xf "{zip_path}" -C "%EXTRACT_DIR%"
if errorlevel 1 (
    powershell -NoProfile -Command "Expand-Archive -Path '{zip_path}' -DestinationPath '%EXTRACT_DIR%' -Force"
)

echo [3/4] Memasang file pembaruan (Konfigurasi & API key Anda tetap aman)...
set "SOURCE_DIR=%EXTRACT_DIR%"
if exist "%EXTRACT_DIR%\\DavisLingo" set "SOURCE_DIR=%EXTRACT_DIR%\\DavisLingo"

:: Salin semua file baru tanpa menimpa config.json pengguna
robocopy "%SOURCE_DIR%" "{app_dir}" /E /XF config.json /R:3 /W:1 /NJH /NJS >nul

:: Jika config.json belum ada di folder tujuan, salin config bawaan
if not exist "{app_dir}\\config.json" (
    if exist "%SOURCE_DIR%\\config.json" (
        copy /y "%SOURCE_DIR%\\config.json" "{app_dir}\\config.json" >nul
    )
)

echo [4/4] Membuka kembali DavisLingo versi terbaru...
timeout /t 1 /nobreak >nul

:: Bersihkan file sementara
if exist "%EXTRACT_DIR%" rd /s /q "%EXTRACT_DIR%" >nul 2>&1
if exist "{zip_path}" del /f /q "{zip_path}" >nul 2>&1

start "" "{app_dir}\\DavisLingo.exe"

echo.
echo Pembaruan selesai!
timeout /t 2 /nobreak >nul
exit
"""
        with open(runner_bat, "w", encoding="utf-8") as bf:
            bf.write(bat_content)

        # Launch runner in independent detached process
        subprocess.Popen(
            ["cmd.exe", "/c", runner_bat],
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
