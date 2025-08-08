# -*- coding: utf-8 -*-

# =================================================================================================
# SCRIPT OTOMATISASI PEMBUATAN AKUN GOOGLE DENGAN CAMOUFOX
# Versi: 7.0 (Edisi Final - Penanganan Alur Dinamis)
#
# DESKRIPSI:
# Versi ini secara cerdas mendeteksi dan menangani alur pendaftaran Google yang
# tidak terduga (misalnya, halaman "How you'll sign in" yang muncul lebih awal),
# membuatnya sangat andal terhadap perubahan UI.
# =================================================================================================

from camoufox.sync_api import Camoufox
from playwright.sync_api import Page, TimeoutError
from browserforge.fingerprints import Screen
from faker import Faker
import time
import random
import csv
import sys
from datetime import datetime

# --- KONFIGURASI UTAMA ---
FILE_EMAIL_PEMULIHAN = 'recovery_emails.txt'
FILE_AKUN_BERHASIL = 'akun_berhasil.csv'
URL_PENDAFTARAN = 'https://accounts.google.com/signup/v2/webcreateaccount?flowName=GlifWebSignIn&flowEntry=SignUp&hl=en'
HEADLESS_MODE = False
DEFAULT_TIMEOUT = 60000 # Waktu tunggu diperpanjang (ditingkatkan)

# --- KONFIGURASI FINGERPRINT ---
SUPPORTED_OS = "windows"
SUPPORTED_WEBGL = {
    "windows": [
        ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA, NVIDIA GeForce GTX 980 Direct3D11 vs_5_0 ps_5_0), or similar"),
        ("Google Inc. (Intel)", "ANGLE (Intel, Intel(R) HD Graphics Direct3D11 vs_5_0 ps_5_0), or similar"),
        ("Google Inc. (AMD)", "ANGLE (AMD, Radeon R9 200 Series Direct3D11 vs_5_0 ps_5_0), or similar"),
    ],
}

# --- Inisialisasi Global ---
fake = Faker()
fingerprint_os = ""
webgl_config = ()

# --- FUNGSI HELPER & LOGGING ---
def log_action(level, message):
    print(f"[{level.upper()}] {message}")

def human_like_delay(min_seconds=1.0, max_seconds=3.0):
    time.sleep(random.uniform(min_seconds, max_seconds))

def get_email_pemulihan():
    try:
        with open(FILE_EMAIL_PEMULIHAN, 'r') as f:
            emails = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        if not emails:
            log_action("fatal", f"File '{FILE_EMAIL_PEMULIHAN}' kosong.")
            return None
        return random.choice(emails)
    except FileNotFoundError:
        log_action("fatal", f"File '{FILE_EMAIL_PEMULIHAN}' tidak ditemukan.")
        return None

def simpan_akun(username, password, email_pemulihan):
    global fingerprint_os, webgl_config
    with open(FILE_AKUN_BERHASIL, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if f.tell() == 0:
            writer.writerow(['Username', 'Password', 'Email Pemulihan', 'OS Fingerprint', 'WebGL Renderer'])
        writer.writerow([username, password, email_pemulihan, fingerprint_os, webgl_config[1]])
    log_action("success", f"Akun {username} berhasil dibuat dan disimpan.")

# --- FUNGSI INTERAKSI ---
def robust_click(page: Page, selector: str, description: str, timeout=DEFAULT_TIMEOUT):
    human_like_delay(0.7, 1.5)
    log_action("action", f"Mencoba mengklik '{description}'")
    log_action("detail", f"Selector: {selector}")
    try:
        locator = page.locator(selector)
        locator.wait_for(state='visible', timeout=timeout)
        locator.scroll_into_view_if_needed()
        human_like_delay(0.5, 1.0)
        locator.click(timeout=8000)
        log_action("ok", f"Berhasil mengklik '{description}'.")
    except Exception as e:
        log_action("error", f"Gagal saat mengklik '{description}': {e}")
        raise

def robust_fill(page: Page, selector: str, text: str, description: str, timeout=DEFAULT_TIMEOUT):
    human_like_delay(0.7, 1.5)
    log_action("action", f"Mencoba mengisi '{description}'")
    log_action("detail", f"Selector: {selector}")
    try:
        locator = page.locator(selector)
        locator.wait_for(state='visible', timeout=timeout)
        locator.scroll_into_view_if_needed()
        human_like_delay(0.5, 1.0)
        locator.press_sequentially(text, delay=random.uniform(90, 230))
        log_action("ok", f"Berhasil mengisi '{description}'.")
    except Exception as e:
        log_action("error", f"Gagal saat mengisi '{description}': {e}")
        raise

# --- FUNGSI LANGKAH-LANGKAH PENDAFTARAN ---

def step_1_fill_name(page: Page):
    log_action("step", "1/7 - Mengisi Nama Pengguna")
    nama_depan = fake.first_name()
    nama_belakang = fake.last_name()
    gender_choice = random.choice(['male', 'female'])
    log_action("info", f"Nama Dihasilkan: {nama_depan} {nama_belakang} (Target Gender: {gender_choice})")
    robust_fill(page, 'input[name="firstName"]', nama_depan, "Nama Depan")
    robust_fill(page, 'input[name="lastName"]', nama_belakang, "Nama Belakang")
    human_like_delay()
    robust_click(page, 'button:has-text("Next")', "Tombol Next (Nama)")
    return nama_depan, nama_belakang, gender_choice

def step_2_fill_basic_info(page: Page, gender_choice: str):
    log_action("step", "2/7 - Mengisi Informasi Dasar")
    page.wait_for_selector('#day', timeout=DEFAULT_TIMEOUT)
    day = str(random.randint(1, 28))
    year = str(random.randint(1990, 2003))
    month_value = str(random.randint(1, 12))
    
    robust_fill(page, '#day', day, "Hari Lahir")
    
    log_action("action", "Memilih bulan menggunakan navigasi keyboard")
    robust_click(page, '#month', "Dropdown Bulan")
    human_like_delay(0.8, 1.5)
    press_count = int(month_value) -1
    if press_count > 0:
        for _ in range(press_count):
            page.keyboard.press('ArrowDown')
            time.sleep(random.uniform(0.1, 0.3))
    page.keyboard.press('Enter')
    log_action("ok", "Berhasil memilih bulan.")
    
    robust_fill(page, '#year', year, "Tahun Lahir")
    
    log_action("action", "Memilih gender menggunakan navigasi keyboard")
    robust_click(page, '#gender', "Dropdown Gender")
    human_like_delay(0.8, 1.5)
    press_count = 1 if gender_choice == 'female' else 2
    for _ in range(press_count):
        page.keyboard.press('ArrowDown')
        time.sleep(random.uniform(0.2, 0.5))
    page.keyboard.press('Enter')
    log_action("ok", "Berhasil memilih gender.")
    
    human_like_delay()
    robust_click(page, 'button:has-text("Next")', "Tombol Next (Info Dasar)")

def step_3_handle_dynamic_username(page: Page, nama_depan: str, nama_belakang: str):
    log_action("step", "3/7 - Penanganan Alur Username Dinamis")
    
    max_retries = 3
    for i in range(max_retries):
        try:
            # Tunggu salah satu dari dua elemen utama muncul
            page.wait_for_selector(
                'input[name="Username"], div[jsname="j9BaPc"]',
                timeout=20000
            )

            username_base = f"{nama_depan.lower().replace(' ', '')}{nama_belakang.lower().replace(' ', '')}{random.randint(100, 9999)}"

            # Opsi 1: Muncul halaman saran email
            suggestion_selector = page.locator('div[jsname="j9BaPc"]')
            if suggestion_selector.count() > 0:
                log_action("info", "Alur Terdeteksi: 'Choose your Gmail address' (Saran)")
                # Ambil username dari saran pertama dan klik
                username_base = suggestion_selector.first.text_content().strip()
                robust_click(suggestion_selector.first, "Saran Email Pertama")
                log_action("info", f"Username yang Dipilih dari saran: {username_base}")
                robust_click(page, 'button:has-text("Next")', "Tombol Next (Setelah Pilih Saran)")
                return username_base

            # Opsi 2: Muncul halaman untuk mengisi username manual
            username_input = page.locator('input[name="Username"]')
            if username_input.is_visible():
                log_action("info", "Alur Terdeteksi: 'How you'll sign in' (Input Manual)")
                robust_fill(page, 'input[name="Username"]', username_base, "Input Username Manual")
                log_action("info", f"Username yang Dibuat: {username_base}")
                robust_click(page, 'button:has-text("Next")', "Tombol Next (Setelah Input Manual)")
                return username_base

        except TimeoutError:
            log_action("warn", f"Timeout saat menunggu elemen username (percobaan {i+1}/{max_retries}).")
            if "myaccount.google.com" in page.url:
                 log_action("success", "Tampaknya sudah berhasil, melewati langkah username.")
                 return "username_tidak_diketahui" # Return placeholder
            page.reload() # Coba muat ulang halaman
            continue
        except Exception as e:
            if "closed" in str(e).lower():
                log_action("fatal", f"Halaman ditutup saat menangani username: {e}")
                raise
            log_action("error", f"Error tak terduga di langkah username: {e}")
            raise

    log_action("fatal", "Gagal menangani alur username setelah beberapa percobaan.")
    raise Exception("Could not handle the dynamic username flow.")

def step_4_and_onwards(page: Page, email_pemulihan: str, username_base: str):
    log_action("step", "4/7 - Membuat Kata Sandi")
    page.wait_for_selector('input[name="Passwd"]', timeout=DEFAULT_TIMEOUT)
    password = fake.password(length=14, special_chars=True, digits=True, upper_case=True, lower_case=True) + "$"
    robust_fill(page, 'input[name="Passwd"]', password, "Input Password")
    robust_fill(page, '#confirm-passwd input', password, "Input Konfirmasi Password")
    human_like_delay()
    robust_click(page, 'button:has-text("Next")', "Tombol Next (Password)")

    # --- Alur Dinamis Pasca-Password ---
    end_of_flow = False
    max_steps = 6  # Maksimal langkah untuk menghindari loop tak terbatas
    current_step = 0

    while not end_of_flow and current_step < max_steps:
        current_step += 1
        log_action("info", f"Memeriksa alur dinamis pasca-password (Langkah {current_step}/{max_steps})")
        
        try:
            # Periksa apakah halaman ditutup
            if page.is_closed():
                log_action("fatal", "Halaman ditutup secara tak terduga. Kemungkinan terdeteksi sebagai bot.")
                raise Exception("Page closed unexpectedly.")

            # Opsi 1: Halaman Email Pemulihan
            recovery_input = page.locator('input[type="email"]')
            if recovery_input.is_visible(timeout=5000):
                log_action("step", "5/7 - Mengisi Email Pemulihan")
                robust_fill(page, 'input[type="email"]', email_pemulihan, "Email Pemulihan")
                robust_click(page, 'button:has-text("Next"), button:has-text("Skip")', "Next/Skip Email Pemulihan")
                continue

            # Opsi 2: Halaman Nomor Telepon
            skip_button = page.locator('button:has-text("Skip")')
            if skip_button.is_visible(timeout=5000):
                log_action("step", "6/7 - Melewati Tambah Nomor Telepon")
                robust_click(page, 'button:has-text("Skip")', "Tombol Skip Telepon")
                continue
            
            # Opsi 3: Halaman Tinjau Akun
            review_button = page.locator('button:has-text("Next")')
            # Periksa konteks untuk memastikan ini adalah tombol "Next" yang benar
            if review_button.is_visible(timeout=5000) and page.locator('div[jsname="B34EJ"]').is_visible(timeout=1000):
                 log_action("step", "7/7 - Meninjau Info Akun")
                 robust_click(page, 'button:has-text("Next")', "Tombol Next (Tinjau Akun)")
                 continue

            # Opsi 4: Halaman Persetujuan (I Agree)
            agree_button = page.locator('button:has-text("I agree")')
            if agree_button.is_visible(timeout=5000):
                log_action("step", "8/8 - Persetujuan Privasi")
                robust_click(page, 'button:has-text("I agree")', "Tombol I Agree")
                end_of_flow = True # Ini adalah langkah interaktif terakhir
                continue
            
            # Opsi 5: Sudah di halaman akun (berhasil)
            if "myaccount.google.com" in page.url:
                log_action("success", "Telah mencapai halaman akun. Pendaftaran berhasil.")
                end_of_flow = True
                continue

            log_action("warn", "Tidak ada elemen yang dikenal terdeteksi. Menunggu sejenak...")
            page.wait_for_timeout(3000) # Tunggu sebentar jika halaman sedang memuat

        except Exception as e:
            if "closed" in str(e).lower():
                log_action("fatal", f"Browser atau halaman ditutup: {e}")
                raise
            log_action("warn", f"Terjadi error pada pemeriksaan alur dinamis: {e}. Melanjutkan...")
    
    if not end_of_flow:
        log_action("fatal", "Gagal menyelesaikan alur pendaftaran setelah beberapa percobaan.")
        raise Exception("Could not complete the dynamic registration flow.")

    # Tunggu konfirmasi akhir
    page.wait_for_url('**myaccount.google.com**', timeout=40000)
    log_action("success", "Pendaftaran berhasil dikonfirmasi!")
    simpan_akun(f"{username_base}@gmail.com", password, email_pemulihan)

# --- FUNGSI UTAMA ---
def main():
    page = None
    email_pemulihan = get_email_pemulihan()
    if not email_pemulihan: sys.exit(1)

    global fingerprint_os, webgl_config
    fingerprint_os = SUPPORTED_OS
    webgl_config = random.choice(SUPPORTED_WEBGL[fingerprint_os])
    screen_config = Screen(min_width=1366, max_width=1920, min_height=768, max_height=1080)
    
    print("="*60)
    log_action("init", "Memulai Sesi Pembuatan Akun Google v7.0")
    log_action("info", f"OS: {fingerprint_os.capitalize()}, WebGL: {webgl_config[1]}")
    print("="*60)

    try:
        with Camoufox(os=fingerprint_os, webgl_config=webgl_config, screen=screen_config, headless=HEADLESS_MODE) as browser:
            page = browser.new_page()
            page.goto(URL_PENDAFTARAN, wait_until="domcontentloaded")

            nama_depan, nama_belakang, gender = step_1_fill_name(page)
            step_2_fill_basic_info(page, gender)
            username = step_3_handle_dynamic_username(page, nama_depan, nama_belakang)
            step_4_and_onwards(page, email_pemulihan, username)

    except Exception as e:
        log_action("fatal", f"PROSES GAGAL TOTAL: {e}")
    finally:
        if page and not page.is_closed():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = f"error_screenshot_{timestamp}.png"
            try:
                page.screenshot(path=screenshot_path)
                log_action("debug", f"Screenshot error disimpan di: {screenshot_path}")
            except Exception as se:
                log_action("debug", f"Gagal menyimpan screenshot: {se}")
        
        print("\nProses selesai. Tekan Enter untuk keluar.")
        input()

if __name__ == '__main__':
    main()
