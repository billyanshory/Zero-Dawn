import math
import os
import random
import re
from enum import Enum, auto
from types import SimpleNamespace
from urllib.parse import parse_qsl, urlsplit, urlunsplit, urlencode
import textwrap
import sys
import uuid
import json
import time

# Pastikan user menginstall library ini: pip install requests
try:
    import requests
except ImportError:
    # Fallback dummy jika requests tidak ada, agar code tidak crash saat compile check,
    # tapi user wajib install.
    class requests:
        def post(url, json, timeout): raise ImportError("Library 'requests' not installed.")
        class exceptions:
            class RequestException(Exception): pass

import pygame
import pymunk
from pygame.math import Vector2
import webbrowser

# ==============================================================================
# KONFIGURASI LISENSI
# ==============================================================================
# GANTI URL INI DENGAN URL FLASK APP KAMU DI PYTHONANYWHERE
LICENSE_SERVER_URL = "http://b1l14n50r1.pythonanywhere.com"
LICENSE_FILE = "license.dat"

def show_splash_screen():
    """
    Menampilkan Box Loading putih ala Microsoft Word LTSC.
    Durasi: 10-15 detik.
    Menggunakan borderless window (NOFRAME) agar terlihat mengambang di desktop.
    """
    # Center window
    os.environ['SDL_VIDEO_CENTERED'] = '1'
    
    # Konfigurasi Box
    box_w, box_h = 600, 350
    
    # Buat screen khusus untuk splash (NOFRAME)
    splash_screen = pygame.display.set_mode((box_w, box_h), pygame.NOFRAME)
    
    clock = pygame.time.Clock()
    
    # Warna
    white = (255, 255, 255)
    light_blue_bg = (230, 240, 255) # Kotak kecil pembungkus tulisan
    blue_text = (0, 50, 150)
    gray_text = (100, 100, 100)
    
    # Font
    try:
        font_header_path = os.path.join("Plus_Jakarta_Sans", "PlusJakartaSans-Regular.ttf")
        font_powered_path = os.path.join("Plus_Jakarta_Sans", "PlusJakartaSans-Bold.ttf")
        if os.path.exists(font_header_path) and os.path.exists(font_powered_path):
            font_header = pygame.font.Font(font_header_path, 20)
            font_powered = pygame.font.Font(font_powered_path, 12)
        else:
            raise Exception("Font not found")
    except:
        font_header = pygame.font.SysFont("arial", 20)
        font_powered = pygame.font.SysFont("arial", 12, bold=True)
    
    # Load Logo
    logo_img = None
    try:
        logo_path = os.path.join(os.path.dirname(__file__), "ikon_rss.png")
        if os.path.exists(logo_path):
            logo_img = pygame.image.load(logo_path).convert_alpha()
            # Scale logo
            logo_img = pygame.transform.smoothscale(logo_img, (100, 100))
    except:
        pass
    
    start_ticks = pygame.time.get_ticks()
    duration = 12000 # 12 detik
    
    # Koordinat relatif terhadap window 600x350
    min_rect = pygame.Rect(box_w - 70, 10, 30, 30)
    close_rect = pygame.Rect(box_w - 35, 10, 30, 30)
    
    while True:
        elapsed = pygame.time.get_ticks() - start_ticks
        if elapsed > duration:
            break
            
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if close_rect.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()
                elif min_rect.collidepoint(event.pos):
                    pygame.display.iconify()
                
        # Gambar Box Putih (Fill seluruh screen karena borderless)
        splash_screen.fill(white)
        pygame.draw.rect(splash_screen, (200, 200, 200), (0, 0, box_w, box_h), 1) # Border halus pinggir
        
        # 1. Header Kiri (Solar System Simulation)
        # Kotak biru muda kecil
        header_text = "Solar System Simulation"
        txt_surf = font_header.render(header_text, True, blue_text)
        header_bg_w = txt_surf.get_width() + 20
        header_bg_h = txt_surf.get_height() + 10
        # Relatif 20,20
        header_bg_rect = pygame.Rect(20, 20, header_bg_w, header_bg_h)
        
        pygame.draw.rect(splash_screen, light_blue_bg, header_bg_rect)
        splash_screen.blit(txt_surf, txt_surf.get_rect(center=header_bg_rect.center))
        
        # 2. Fitur Minimize dan Close (Kanan Atas)
        # Simbol Minimize
        pygame.draw.line(splash_screen, (50, 50, 50), (min_rect.centerx - 5, min_rect.centery), (min_rect.centerx + 5, min_rect.centery), 2)
        
        # X Close
        start_x, start_y = close_rect.centerx - 5, close_rect.centery - 5
        end_x, end_y = close_rect.centerx + 5, close_rect.centery + 5
        pygame.draw.line(splash_screen, (50, 50, 50), (start_x, start_y), (end_x, end_y), 2)
        pygame.draw.line(splash_screen, (50, 50, 50), (start_x, end_y), (end_x, start_y), 2)
        
        # 3. Logo Tengah
        center_x, center_y = box_w // 2, box_h // 2
        if logo_img:
            logo_rect = logo_img.get_rect(center=(center_x, center_y))
            splash_screen.blit(logo_img, logo_rect)
        else:
            # Fallback Text logo
            fallback_font = pygame.font.SysFont("arial", 40, bold=True)
            f_surf = fallback_font.render("RSS", True, (200, 200, 200))
            splash_screen.blit(f_surf, f_surf.get_rect(center=(center_x, center_y)))
            
        # 4. Tulisan Powered by (Bawah Logo)
        pow_text = "Powered by PT. Nurul Hidayah Arbie"
        pow_surf = font_powered.render(pow_text, True, gray_text)
        pow_rect = pow_surf.get_rect(center=(center_x, center_y + 70))
        splash_screen.blit(pow_surf, pow_rect)
        
        # 5. Tulisan Pojok Kiri Bawah
        loading_txt = "Solar System Simulation"
        load_surf = font_powered.render(loading_txt, True, gray_text)
        splash_screen.blit(load_surf, (20, box_h - 30))
        
        # Loading dots animation
        dots = "." * (int(elapsed / 500) % 4)
        start_txt = f"Starting{dots}"
        start_surf = font_powered.render(start_txt, True, gray_text)
        splash_screen.blit(start_surf, (20, box_h - 50))
        
        pygame.display.flip()
        clock.tick(30)

def get_hwid():
    """Mendapatkan Hardware ID unik berdasarkan MAC Address."""
    return str(uuid.getnode())

class LicenseState(Enum):
    CHECKING = auto()
    INPUT_KEY = auto()
    ACTIVATING = auto()
    SUCCESS = auto()
    FAILED = auto()
    LICENSED = auto()

# ==============================================================================

# Default window size; updated on resize events
WIDTH, HEIGHT = 1280, 720
VERTICAL_SCALE = 0.5
SPEED_OPTIONS = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
KEYBOARD_BTN_INACTIVE = (211, 211, 211)
KEYBOARD_BTN_ACTIVE = (173, 216, 230)
DATA_BUTTON_SIZE = 36

# Camera movement configuration
PAN_SPEED_WORLD = 200.0
PAN_SPEED_MODE = "world"
DIAGONAL_NORMALIZE = True

ZOOM_EPSILON = 1e-9
LOD_ZOOM = 0.02

SUN_RADIUS = 20
ORBIT_SCALE_DEFAULT = 0.75
SUN_DRAW_RADIUS = SUN_RADIUS * ORBIT_SCALE_DEFAULT

USE_APPROX_ORBITS: bool = True

APPROX_ORBIT_RADII = {
    "Mercury": 80,
    "Venus": 130,
    "Earth": 185,
    "Mars": 250,
    "Jupiter": 340,
    "Saturn": 440,
    "Uranus": 560,
    "Neptune": 690,
    "Pluto": 820,
}

BASE_INNER_RADIUS = 80
ORBIT_VISUAL_BUFFER = 8

SHOW_WELL = True
WELL_A = 100.0
WELL_R0 = 100.0
WELL_MAX_DEPTH = 150.0

SEGMENT_DISTANCES = [
    57.9, 50.3, 41.4, 78.4, 550.5, 653.5, 1435.0, 1648.0,
]

SEGMENT_LABELS = {
    "en": ["57.9 million km", "50.3 million km", "41.4 million km", "78.4 million km", "550.5 million km", "653.5 million km", "1,435.0 million km", "1,648.0 million km"],
    "id": ["57,9 juta km", "50,3 juta km", "41,4 juta km", "78,4 juta km", "550,5 juta km", "653,5 juta km", "1.435 juta km", "1.648 juta km"],
}

ORBIT_PADDING = 2
DISTANCE_DATA = []
OUTER_ORBIT_RADIUS = 0.0

CURRENT_LANG = "id"

TEXTS = {
    "keyboard_functions": {"id": "Fungsi Keyboard", "en": "Keyboard Functions"},
    "play": {"id": "Putar", "en": "Play"},
    "pause": {"id": "Jeda", "en": "Pause"},
    "lang_button": {"id": "Bahasa/Language", "en": "Bahasa/Language"},
    "key_w": {"id": "'W' untuk menggerakkan kamera ke atas", "en": "'W' move camera up"},
    "key_s": {"id": "'S' untuk ke bawah", "en": "'S' move camera down"},
    "key_a": {"id": "'A' untuk ke kiri", "en": "'A' move camera left"},
    "key_d": {"id": "'D' untuk ke kanan", "en": "'D' move camera right"},
    "key_lr": {"id": "Panah kiri/kanan untuk merotasi tata surya", "en": "Left/Right arrows rotate the system"},
    "key_ud": {"id": "Panah atas/bawah untuk zoom in dan zoom out", "en": "Up/Down arrows zoom in/out"},
    "key_wheel": {"id": "Gulir mouse untuk zoom cepat (in/out)", "en": "Mouse scroll — fast zoom in/out"},
    "key_r": {"id": "'R' untuk mereset sudut kamera", "en": "'R' reset camera angle"},
    "key_backspace": {"id": "Backspace untuk reset tata surya", "en": "Backspace resets the solar system"},
    "key_space": {"id": "'Spasi' untuk pause atau lanjutkan simulasi", "en": "Space to pause/resume simulation"},
    "key_f11": {"id": "F11 — Toggle Fullscreen", "en": "F11 — Toggle Fullscreen"},
    "angle_0": {"id": "Sudut 0°", "en": "Angle 0°"},
    "angle_90": {"id": "Sudut 90°", "en": "Angle 90°"},
    "angle_45": {"id": "Sudut 45° (Default)", "en": "Angle 45° (Default)"},
    "diameter_lbl": {"id": "DIAMETER", "en": "DIAMETER"},
    "distance_lbl": {"id": "JARAK RATA-RATA DARI MATAHARI", "en": "AVERAGE DISTANCE FROM SUN"},
    "distance_lbl_sun": {"id": "JARAK RATA-RATA DARI INTI GALAKSI BIMA SAKTI", "en": "AVERAGE DISTANCE FROM THE CORE OF THE MILKY WAY"},
    "period_lbl": {"id": "PERIODE ORBIT", "en": "ORBITAL PERIOD"},
    "speed_lbl": {"id": "KECEPATAN ORBIT", "en": "ORBITAL SPEED"},
    "life_lbl": {"id": "KEHIDUPAN", "en": "LIFE"},
    "hint_close": {"id": "Esc untuk menutup • F11 layar penuh", "en": "Esc to close • F11 fullscreen"},
    "sources_title": {"id": "Sumber Data", "en": "Data References"},
    "sources_tooltip": {"id": "Sumber data", "en": "Data references"},
    "time_info_title": {"id": "Konversi Waktu Simulasi", "en": "Simulation Time Conversion"},
    "time_info_body": {
        "id": "waktu periode planet dalam mengelilingi matahari di simulasi ini disederhanakan dengan cara dikonversi menjadi 10 hari di dunia nyata dihitung 1 detik di waktu simulasi berjalan, sehingga tidak terlalu lama kita menunggu periode pergerakan revolusi tiap planet dalam mengelilingi matahari; maka jika Bumi membutuhkan waktu '365 hari' untuk sekali revolusi → dikonversi menjadi 1 hari = 1 detik, maka akan menjadi '365 detik' → dikonversi lagi menjadi 10 hari = 1 detik, maka akan menjadi '36.5 detik'.",
        "en": "In this simulation, we compress time: every 10 real-world days equals 1 simulation second. This lets you see orbits progress quickly. For example, Earth's orbital period is 365 days. First, mapping 1 real-world day → 1 sim second gives 365 seconds. Then applying 10 days → 1 sim second compresses it further to 36.5 seconds.",
    },
    "sketch_btn": {"id": "Mode Sketsa", "en": "Sketch Mode"},
}

def t(key: str) -> str:
    return TEXTS[key][CURRENT_LANG]

def open_url(url: str) -> None:
    webbrowser.open_new_tab(url)

EXACT_SOURCES_ID = """
1. * 'Diameter planet (km)' -> 'NASA NSSDCA — Planetary Fact Sheet (Metric): [https://nssdc.gsfc.nasa.gov/planetary/factsheet/](https://nssdc.gsfc.nasa.gov/planetary/factsheet/)'
2. * 'Jarak rata-rata planet dari Matahari (… juta/million km)' -> 'NASA NSSDCA — Planetary Fact Sheet (Metric): [https://nssdc.gsfc.nasa.gov/planetary/factsheet/](https://nssdc.gsfc.nasa.gov/planetary/factsheet/)'
3. * 'Periode orbit planet (hari/tahun)' -> 'NASA NSSDCA — Planetary Fact Sheet (Metric): [https://nssdc.gsfc.nasa.gov/planetary/factsheet/](https://nssdc.gsfc.nasa.gov/planetary/factsheet/)'
4. * 'Kecepatan orbit planet (km/s; dikonversi ke km/jam ×3600)' -> 'NASA NSSDCA — Planetary Fact Sheet (Metric) + Notes: [https://nssdc.gsfc.nasa.gov/planetary/factsheet/](https://nssdc.gsfc.nasa.gov/planetary/factsheet/)  |  [https://nssdc.gsfc.nasa.gov/planetary/factsheet/planetfact_notes.html](https://nssdc.gsfc.nasa.gov/planetary/factsheet/planetfact_notes.html)'
5. * 'Istilah & satuan (definisi Orbital Velocity, AU, dsb.)' -> 'NASA NSSDCA — Planetary Fact Sheet Notes: [https://nssdc.gsfc.nasa.gov/planetary/factsheet/planetfact_notes.html](https://nssdc.gsfc.nasa.gov/planetary/factsheet/planetfact_notes.html)'
6. * 'Ringkasan/deskripsi populer tiap planet (Mercury…Neptune)' -> 'NASA Science — Planet “Facts” pages: Mercury [https://science.nasa.gov/mercury/facts/](https://science.nasa.gov/mercury/facts/)  |  Venus [https://science.nasa.gov/venus/venus-facts/](https://science.nasa.gov/venus/venus-facts/)  |  Earth [https://science.nasa.gov/earth/facts/](https://science.nasa.gov/earth/facts/)  |  Mars [https://science.nasa.gov/mars/facts/](https://science.nasa.gov/mars/facts/)  |  Jupiter [https://science.nasa.gov/jupiter/jupiter-facts/](https://science.nasa.gov/jupiter/jupiter-facts/)  |  Saturn [https://science.nasa.gov/saturn/facts/](https://science.nasa.gov/saturn/facts/)  |  Uranus [https://science.nasa.gov/uranus/facts/](https://science.nasa.gov/uranus/facts/)  |  Neptune [https://science.nasa.gov/neptune/neptune-facts/](https://science.nasa.gov/neptune/neptune-facts/)'
7. * 'Sifat fisik Matahari (rasio massa, diameter ~109× Bumi, suhu efektif, dsb.)' -> 'NASA NSSDCA — Sun Fact Sheet: [https://nssdc.gsfc.nasa.gov/planetary/factsheet/sunfact.html](https://nssdc.gsfc.nasa.gov/planetary/factsheet/sunfact.html)  |  NASA Science — Sun: Facts: [https://science.nasa.gov/sun/facts/](https://science.nasa.gov/sun/facts/)'
8. * 'Jarak Matahari ke inti Bima Sakti (≈26–28 ribu tahun cahaya)' -> 'NASA SVS (Milky Way Center): [https://svs.gsfc.nasa.gov/30961](https://svs.gsfc.nasa.gov/30961)  |  NASA StarChild (Q&A 28,000 ly): [https://starchild.gsfc.nasa.gov/docs/StarChild/questions/question18.html](https://starchild.gsfc.nasa.gov/docs/StarChild/questions/question18.html)'
9. * 'Periode orbit galaktik Matahari (Galactic year ≈230 juta tahun; rentang 225–250 Myr)' -> 'NASA Science — Solar System Facts: [https://science.nasa.gov/solar-system/solar-system-facts/](https://science.nasa.gov/solar-system/solar-system-facts/)  |  NASA StarChild — The Milky Way: [https://starchild.gsfc.nasa.gov/docs/StarChild/universe_level2/milky_way.html](https://starchild.gsfc.nasa.gov/docs/StarChild/universe_level2/milky_way.html)'
10. * 'Status kehidupan (pernyataan umum “belum ada bukti kehidupan di luar Bumi”)' -> 'NASA — artikel ringkas: [https://www.nasa.gov/missions/nasa-is-taking-a-new-look-at-searching-for-life-beyond-earth/](https://www.nasa.gov/missions/nasa-is-taking-a-new-look-at-searching-for-life-beyond-earth/)'
11. * 'Penentuan label bahasa jarak “… million km” / “… juta km” pada UI' -> 'Diturunkan dari kolom Distance from Sun (10^6 km) — NASA NSSDCA Planetary Fact Sheet (Metric): [https://nssdc.gsfc.nasa.gov/planetary/factsheet/](https://nssdc.gsfc.nasa.gov/planetary/factsheet/)'
12. * 'Catatan praktik: konversi km/s → km/jam untuk UI' -> 'Gunakan ×3600; rujukan definisi di NASA NSSDCA — Planetary Fact Sheet Notes: [https://nssdc.gsfc.nasa.gov/planetary/factsheet/planetfact_notes.html](https://nssdc.gsfc.nasa.gov/planetary/factsheet/planetfact_notes.html)'
"""

EXACT_SOURCES_EN = """
1. * 'Planet diameter (km)' -> 'NASA NSSDCA — Planetary Fact Sheet (Metric): [https://nssdc.gsfc.nasa.gov/planetary/factsheet/](https://nssdc.gsfc.nasa.gov/planetary/factsheet/)'
2. * 'Average distance of planets from the Sun (… million km)' -> 'NASA NSSDCA — Planetary Fact Sheet (Metric): [https://nssdc.gsfc.nasa.gov/planetary/factsheet/](https://nssdc.gsfc.nasa.gov/planetary/factsheet/)'
3. * 'Orbital period of planets (days/years)' -> 'NASA NSSDCA — Planetary Fact Sheet (Metric): [https://nssdc.gsfc.nasa.gov/planetary/factsheet/](https://nssdc.gsfc.nasa.gov/planetary/factsheet/)'
4. * 'Orbital speed of planets (km/s; converted to km/h ×3600)' -> 'NASA NSSDCA — Planetary Fact Sheet (Metric) + Notes: [https://nssdc.gsfc.nasa.gov/planetary/factsheet/](https://nssdc.gsfc.nasa.gov/planetary/factsheet/)  |  [https://nssdc.gsfc.nasa.gov/planetary/factsheet/planetfact_notes.html](https://nssdc.gsfc.nasa.gov/planetary/factsheet/planetfact_notes.html)'
5. * 'Terms & units (definitions of Orbital Velocity, AU, etc.)' -> 'NASA NSSDCA — Planetary Fact Sheet Notes: [https://nssdc.gsfc.nasa.gov/planetary/factsheet/planetfact_notes.html](https://nssdc.gsfc.nasa.gov/planetary/factsheet/planetfact_notes.html)'
6. * 'Popular summary/description of each planet (Mercury…Neptune)' -> 'NASA Science — Planet “Facts” pages: Mercury [https://science.nasa.gov/mercury/facts/](https://science.nasa.gov/mercury/facts/)  |  Venus [https://science.nasa.gov/venus/venus-facts/](https://science.nasa.gov/venus/venus-facts/)  |  Earth [https://science.nasa.gov/earth/facts/](https://science.nasa.gov/earth/facts/)  |  Mars [https://science.nasa.gov/mars/facts/](https://science.nasa.gov/mars/facts/)  |  Jupiter [https://science.nasa.gov/jupiter/jupiter-facts/](https://science.nasa.gov/jupiter/jupiter-facts/)  |  Saturn [https://science.nasa.gov/saturn/facts/](https://science.nasa.gov/saturn/facts/)  |  Uranus [https://science.nasa.gov/uranus/facts/](https://science.nasa.gov/uranus/facts/)  |  Neptune [https://science.nasa.gov/neptune/neptune-facts/](https://science.nasa.gov/neptune/neptune-facts/)'
7. * 'Sun physical properties (mass ratio, diameter ~109× Earth, effective temperature, etc.)' -> 'NASA NSSDCA — Sun Fact Sheet: [https://nssdc.gsfc.nasa.gov/planetary/factsheet/sunfact.html](https://nssdc.gsfc.nasa.gov/planetary/factsheet/sunfact.html)  |  NASA Science — Sun: Facts: [https://science.nasa.gov/sun/facts/](https://science.nasa.gov/sun/facts/)'
8. * 'Sun’s distance to the Milky Way core (≈26–28 thousand light-years)' -> 'NASA SVS (Milky Way Center): [https://svs.gsfc.nasa.gov/30961](https://svs.gsfc.nasa.gov/30961)  |  NASA StarChild (Q&A 28,000 ly): [https://starchild.gsfc.nasa.gov/docs/StarChild/questions/question18.html](https://starchild.gsfc.nasa.gov/docs/StarChild/questions/question18.html)'
9. * 'Sun’s galactic orbital period (Galactic year ≈230 million years; range 225–250 Myr)' -> 'NASA Science — Solar System Facts: [https://science.nasa.gov/solar-system/solar-system-facts/](https://science.nasa.gov/solar-system/solar-system-facts/)  |  NASA StarChild — The Milky Way: [https://starchild.gsfc.nasa.gov/docs/StarChild/universe_level2/milky_way.html](https://starchild.gsfc.nasa.gov/docs/StarChild/universe_level2/milky_way.html)'
10. * 'Life status (general statement “no evidence of life beyond Earth”)' -> 'NASA — brief article: [https://www.nasa.gov/missions/nasa-is-taking-a-new-look-at-searching-for-life-beyond-earth/](https://www.nasa.gov/missions/nasa-is-taking-a-new-look-at-searching-for-life-beyond-earth/)'
11. * 'UI language label decision “… million km” / “… juta km”' -> 'Derived from Distance from Sun (10^6 km) — NASA NSSDCA Planetary Fact Sheet (Metric): [https://nssdc.gsfc.nasa.gov/planetary/factsheet/](https://nssdc.gsfc.nasa.gov/planetary/factsheet/)'
12. * 'Practice note: converting km/s → km/h for UI' -> 'Use ×3600; reference definition in NASA NSSDCA — Planetary Fact Sheet Notes: [https://nssdc.gsfc.nasa.gov/planetary/factsheet/planetfact_notes.html](https://nssdc.gsfc.nasa.gov/planetary/factsheet/planetfact_notes.html)'
"""

def log(msg: str) -> None:
    print(msg, flush=True)

class UIState(Enum):
    RUNNING = auto()
    OVERLAY = auto()
    LANG_MODAL = auto()
    DATA_SOURCES = auto()
    TIME_INFO = auto()
    MARS_BIO = auto() # Kini digunakan untuk semua poin Planet Detail (Mars & Earth)

class AngleMode(Enum):
    SIDE_0 = auto()
    TOP_90 = auto()
    OBLIQUE_45 = auto()

ANGLE_LABEL_KEYS = ["angle_0", "angle_90", "angle_45"]
ANGLE_LABELS = [t(k) for k in ANGLE_LABEL_KEYS]
ANGLE_MODES = [AngleMode.SIDE_0, AngleMode.TOP_90, AngleMode.OBLIQUE_45]

PLANET_INFO = {
    "Sun": {
        "summary_italic": (
            "1. Central Star: The Sun contains 99.86% of the Solar System's total mass.\n"
            "2. Solar Cycle: 2025 is near the Solar Maximum of Cycle 25, showing high activity.\n"
            "3. Structure: A hot plasma sphere emitting light/heat via nuclear fusion.\n"
            "4. Core Temp: Exceeds 15 million degrees Celsius.\n"
            "5. Rotation: It rotates on its axis about once every 27 days.\n"
            "6. Future: In ~5 billion years, it will expand into a Red Giant."
        ),
        "diameter": "\u2248 1,392,684 km (\u2248 109 \xd7 Earth)",
        "distance": "\u2248 27,700 light-years",
        "period": "\u2248 225–250 million years",
        "life": "None (no known life).",
    },
    "Mercury": {
        "summary_italic": (
            "1. Extreme Temperature: Swings from 430\xb0C (day) to -180\xb0C (night).\n"
            "2. Shrinking Planet: Mercury is slowly contracting as its core cools.\n"
            "3. Speedy Orbit: The fastest planet, completing a year in just 88 days.\n"
            "4. Ice Deposits: Water ice exists in permanently shadowed polar craters.\n"
            "5. Surface: Heavily cratered, resembling Earth's Moon.\n"
            "6. Exploration: BepiColombo mission (arrived late 2025) is studying it now."
        ),
        "diameter": "4,879 km",
        "distance": "57.9 million km",
        "period": "88 days",
        "speed": "170,503 km/h",
        "life": "None (no known life).",
    },
    "Venus": {
        "summary_italic": (
            "1. Hottest Planet: Thick CO\u2082 atmosphere traps heat (Runaway Greenhouse).\n"
            "2. Backward Spin: Rotates clockwise (retrograde) very slowly.\n"
            "3. Day > Year: One rotation takes longer than its orbit around the Sun.\n"
            "4. Acid Clouds: Features clouds of sulfuric acid.\n"
            "5. Volcanoes: Active volcanism is suspected on the surface.\n"
            "6. 'Twin': Similar size/structure to Earth, but hellish conditions."
        ),
        "diameter": "12,104 km",
        "distance": "108.2 million km",
        "period": "225 days",
        "speed": "126,074 km/h",
        "life": "None (no known life).",
    },
    "Earth": {
        "summary_italic": (
            "1. Blue Planet: 71% of the surface is covered by liquid water.\n"
            "2. Tectonic Plates: The only planet with active plate tectonics.\n"
            "3. Atmosphere: Nitrogen-Oxygen mix perfect for sustaining life.\n"
            "4. Moon: Has one large natural satellite affecting tides/stability.\n"
            "5. Magnetic Field: Protects surface from harmful solar wind.\n"
            "6. Life: The only known celestial body to support life."
        ),
        "diameter": "12,756 km",
        "distance": "149.6 million km",
        "period": "365.25 days",
        "speed": "107,218 km/h",
        "life": "Humans, animals, and plants",
    },
    "Mars": {
        "summary_italic": (
            "1. Red Planet: Iron oxide (rust) dust gives it the red color.\n"
            "2. Giant Canyon: Valles Marineris is 4x deeper than Grand Canyon.\n"
            "3. Tallest Volcano: Olympus Mons is the largest volcano in the system.\n"
            "4. Thin Air: Atmosphere is 100x thinner than Earth's (mostly CO\u2082).\n"
            "5. Water: Polar ice caps and subsurface brine lakes exist.\n"
            "6. Recent 2025 Discovery: NASA has detected potential microbial biosignatures."
        ),
        "diameter": "6,792 km",
        "distance": "228 million km",
        "period": "687 days",
        "speed": "86,677 km/h",
        "life": "Potential Microbial Evidence (NASA 2025)",
    },
    "Jupiter": {
        "summary_italic": (
            "1. King of Planets: Massive enough to fit 1,300 Earths inside.\n"
            "2. Great Red Spot: A giant storm raging for over 300 years.\n"
            "3. Fast Spin: Shortest day in the solar system (~10 hours).\n"
            "4. Moons: Has over 90 moons, including Ganymede (largest).\n"
            "5. Faint Rings: Has a thin ring system, unlike Saturn's bright ones.\n"
            "6. Magnetic Field: The strongest planetary magnetic field."
        ),
        "diameter": "142,984 km",
        "distance": "778.5 million km",
        "period": "11.9 years (4,331 days)",
        "speed": "47,002 km/h",
        "life": "None (no known life).",
    },
    "Saturn": {
        "summary_italic": (
            "1. Ring System: Most complex/spectacular rings of ice and rock.\n"
            "2. Hexagon Storm: A six-sided jet stream pattern at the north pole.\n"
            "3. Density: Less dense than water; it would float in a giant bathtub.\n"
            "4. Moons: Titan is the only moon with a thick atmosphere.\n"
            "5. Winds: Equatorial winds can reach 1,800 km/h.\n"
            "6. Flattened: Rapid spin causes it to bulge at the equator."
        ),
        "diameter": "120,536 km",
        "distance": "1,432 million km",
        "period": "29.5 years (10,747 days)",
        "speed": "34,701 km/h",
        "life": "None (no known life).",
    },
    "Uranus": {
        "summary_italic": (
            "1. Tilted Giant: Rotates on its side (98-degree axial tilt).\n"
            "2. Coldest Planet: Atmosphere hits -224\xb0C.\n"
            "3. Retrograde: Rotates opposite to most planets (like Venus).\n"
            "4. Blue-Green: Methane in atmosphere absorbs red light.\n"
            "5. Rings: Has 13 known faint rings.\n"
            "6. Moons: Named after characters from Shakespeare and Pope."
        ),
        "diameter": "51,118 km",
        "distance": "2,872.5 million km",
        "period": "84 years (30,589 days)",
        "speed": "24,477 km/h",
        "life": "None (no known life).",
    },
    "Neptune": {
        "summary_italic": (
            "1. Windy Planet: Supersonic winds reach 2,000 km/h.\n"
            "2. Dark Spot: Features shifting giant storms similar to Jupiter.\n"
            "3. Jarak: Cahaya matahari butuh 4 jam untuk sampai ke sini.\n"
            "4. Moon Triton: Orbits in the opposite direction (retrograde).\n"
            "5. Discovery: Mathematical prediction found it before telescopes.\n"
            "6. Color: Vivid blue due to atmospheric methane and unknown compounds."
        ),
        "diameter": "49,528 km",
        "distance": "4,495.1 million km",
        "period": "164.8 years (59,800 days)",
        "speed": "19,566 km/h",
        "life": "None (no known life).",
    },
}

PLANET_INFO_ID = {
    "Sun": {
        "summary_italic": (
            "1. Bintang Pusat: Matahari mengandung 99,86% massa total Tata Surya.\n"
            "2. Siklus Solar: 2025 mendekati Puncak Siklus 25 dengan aktivitas tinggi.\n"
            "3. Struktur: Bola plasma panas, fusi nuklir memancarkan cahaya/panas.\n"
            "4. Suhu Inti: Lebih dari 15 juta derajat Celcius.\n"
            "5. Rotasi: Berputar pada porosnya setiap ~27 hari.\n"
            "6. Masa Depan: Dalam ~5 miliar tahun, akan menjadi Raksasa Merah."
        ),
        "diameter": "\u2248 1.392.684 km (\u2248 109 \xd7 Bumi)",
        "distance": "\u2248 27.700 tahun cahaya",
        "period": "\u2248 225–250 juta tahun",
        "life": "Tidak ada (tidak diketahui adanya kehidupan).",
    },
    "Mercury": {
        "summary_italic": (
            "1. Suhu Ekstrem: Berkisar 430\xb0C (siang) hingga -180\xb0C (malam).\n"
            "2. Menyusut: Merkurius perlahan mengecil saat intinya mendingin.\n"
            "3. Orbit Cepat: Planet tercepat, satu tahun hanya 88 hari.\n"
            "4. Deposit Es: Ada es di kawah kutub yang selalu gelap.\n"
            "5. Permukaan: Penuh kawah, mirip Bulan milik Bumi.\n"
            "6. Eksplorasi: Misi BepiColombo (tiba akhir 2025) sedang menelitinya."
        ),
        "diameter": "4.879 km",
        "distance": "57,9 juta km",
        "period": "88 hari",
        "speed": "170.503 km/jam",
        "life": "Tidak ada (tidak diketahui adanya kehidupan).",
    },
    "Venus": {
        "summary_italic": (
            "1. Planet Terpanas: Atmosfer CO\u2082 tebal memerangkap panas (Efek R.Kaca).\n"
            "2. Putaran Mundur: Berotasi searah jarum jam (retrograde) sangat lambat.\n"
            "3. Hari > Tahun: Satu rotasi lebih lama dari orbitnya mengelilingi Matahari.\n"
            "4. Awan Asam: Memiliki awan asam sulfat yang pekat.\n"
            "5. Gunung Berapi: Diduga masih aktif secara vulkanik.\n"
            "6. 'Kembaran': Ukuran mirip Bumi, tapi kondisinya seperti neraka."
        ),
        "diameter": "12.104 km",
        "distance": "108,2 juta km",
        "period": "225 hari",
        "speed": "126.074 km/jam",
        "life": "Tidak ada (tidak diketahui adanya kehidupan).",
    },
    "Earth": {
        "summary_italic": (
            "1. Planet Biru: 71% permukaan tertutup air cair.\n"
            "2. Lempeng Tektonik: Satu-satunya planet dengan tektonik aktif.\n"
            "3. Atmosfer: Campuran Nitrogen-Oksigen sempurna untuk kehidupan.\n"
            "4. Bulan: Memiliki satu satelit alami besar yang menstabilkan poros.\n"
            "5. Medan Magnet: Melindungi dari angin matahari berbahaya.\n"
            "6. Kehidupan: Satu-satunya benda langit yang diketahui mendukung kehidupan."
        ),
        "diameter": "12.756 km",
        "distance": "149,6 juta km",
        "period": "365,25 hari",
        "speed": "107.218 km/jam",
        "life": "Manusia, hewan, dan tumbuhan",
    },
    "Mars": {
        "summary_italic": (
            "1. Planet Merah: Debu besi oksida (karat) memberinya warna merah.\n"
            "2. Ngarai Raksasa: Valles Marineris 4x lebih dalam dari Grand Canyon.\n"
            "3. Gunung Tertinggi: Olympus Mons adalah gunung berapi terbesar di Tata Surya.\n"
            "4. Atmosfer Tipis: 100x lebih tipis dari Bumi (mayoritas CO\u2082).\n"
            "5. Air: Memiliki tudung es kutub dan danau air asin bawah tanah.\n"
            "6. Penemuan 2025: NASA mendeteksi potensi biosignature mikrobial."
        ),
        "diameter": "6.792 km",
        "distance": "228 juta km",
        "period": "687 hari",
        "speed": "86.677 km/jam",
        "life": "Potensi Bukti Mikrobial (NASA 2025)",
    },
    "Jupiter": {
        "summary_italic": (
            "1. Raja Planet: Cukup besar untuk memuat 1.300 Bumi di dalamnya.\n"
            "2. Titik Merah Besar: Badai raksasa yang mengamuk >300 tahun.\n"
            "3. Rotasi Cepat: Hari terpendek di tata surya (~10 jam).\n"
            "4. Bulan: Memiliki >90 bulan, termasuk Ganymede (terbesar).\n"
            "5. Cincin Tipis: Punya cincin tipis, tidak setebal Saturnus.\n"
            "6. Medan Magnet: Medan magnet planet terkuat."
        ),
        "diameter": "142.984 km",
        "distance": "778,5 juta km",
        "period": "11.9 tahun (4.331 hari)",
        "speed": "47.002 km/jam",
        "life": "Tidak ada (tidak diketahui adanya kehidupan).",
    },
    "Saturn": {
        "summary_italic": (
            "1. Sistem Cincin: Cincin es dan batuan paling spektakuler.\n"
            "2. Badai Heksagon: Pola aliran jet enam sisi di kutub utara.\n"
            "3. Kepadatan: Lebih ringan dari air; bisa mengapung di bak mandi raksasa.\n"
            "4. Bulan: Titan adalah satu-satunya bulan dengan atmosfer tebal.\n"
            "5. Angin: Angin khatulistiwa bisa mencapai 1.800 km/jam.\n"
            "6. Gepeng: Rotasi cepat membuatnya menonjol di khatulistiwa."
        ),
        "diameter": "120.536 km",
        "distance": "1.432 juta km",
        "period": "29.5 tahun (10.747 hari)",
        "speed": "34.701 km/jam",
        "life": "Tidak ada (tidak diketahui adanya kehidupan).",
    },
    "Uranus": {
        "summary_italic": (
            "1. Raksasa Miring: Berotasi menyamping (kemiringan poros 98 derajat).\n"
            "2. Planet Terdingin: Atmosfer mencapai suhu -224\xb0C.\n"
            "3. Retrograde: Berotasi berlawanan arah (seperti Venus).\n"
            "4. Biru-Hijau: Metana di atmosfer menyerap cahaya merah.\n"
            "5. Cincin: Memiliki 13 cincin redup.\n"
            "6. Bulan: Dinamai dari karakter karya Shakespeare dan Pope."
        ),
        "diameter": "51.118 km",
        "distance": "2.872,5 juta km",
        "period": "84 tahun (30.589 hari)",
        "speed": "24.477 km/jam",
        "life": "Tidak ada (tidak diketahui adanya kehidupan).",
    },
    "Neptune": {
        "summary_italic": (
            "1. Planet Berangin: Angin supersonik mencapai 2.000 km/jam.\n"
            "2. Titik Gelap: Memiliki badai raksasa yang berpindah-pindah.\n"
            "3. Jarak: Cahaya matahari butuh 4 jam untuk sampai ke sini.\n"
            "4. Bulan Triton: Mengorbit berlawanan arah rotasi planet (retrograde).\n"
            "5. Penemuan: Ditemukan lewat prediksi matematika, bukan teleskop.\n"
            "6. Warna: Biru cerah akibat metana dan senyawa atmosferik lain."
        ),
        "diameter": "49.528 km",
        "distance": "4.495,1 juta km",
        "period": "164,8 tahun (59.800 hari)",
        "speed": "19.566 km/jam",
        "life": "Tidak ada (tidak diketahui adanya kehidupan).",
    },
}

def get_planet_info(name: str):
    if CURRENT_LANG == "id":
        return PLANET_INFO_ID[name]
    return PLANET_INFO[name]

# ==============================================================================
# MARS BIOSIGNATURE CONTENT & CLASSES (UPDATED FOR ALL 6 POINTS)
# ==============================================================================

# Data struktur untuk konten Mars (Point 1 - 6) - INDONESIA
MARS_DETAILS_CONFIG_ID = {
    1: {
        "title": "PLANET MERAH MARS",
        "img_file": "permukaanmerahMars.png",
        "img_caption": "Red Color is caused by iron oxide (rust) dust covering its surface. Source: Data NASA",
        "link_text": "Red Color caused by rust. Source: Data NASA",
        "link_url": "https://science.nasa.gov/mars/facts/",
        "facts": ["Mars berwarna merah", "Ditutupi oleh debu besi oksida (karat)", "Warna khas yang terlihat jelas dari Bumi"],
        "text": """Bayangkan sebuah dunia di mana besi berkarat bukan tanda kerusakan, melainkan cat dasar seluruh planet. Mars berwarna merah bukan karena panas, tetapi karena oksidasi—sebuah proses kimiawi raksasa yang terjadi selama miliaran tahun, mengubah batuan besi menjadi debu halus berwarna merah darah yang menyelimuti segalanya.

Angin di Mars tidak pernah berhenti bekerja. Ia mengangkat partikel-partikel debu karat ini ke atmosfer, menciptakan langit berwarna merah muda di siang hari dan senja biru yang menghantui. Ini adalah laboratorium kimia alam semesta yang memamerkan keindahan dari reaksi sederhana antara besi dan sisa-sisa oksigen purba.

Menatap Mars di langit malam adalah menatap sejarah geologis yang membeku. Warna merahnya adalah peringatan sekaligus undangan; ia menceritakan kisah planet yang mungkin pernah biru seperti Bumi, sebelum perlahan mengering dan berkarat, meninggalkan monumen abadi bagi waktu dan perubahan."""
    },
    2: {
        "title": "NGARAI RAKSASA \"VALLES MARINERIS\"",
        "img_file": "NgaraiRaksasaVallesMarineris.png",
        "img_caption": "Ngarai Raksasa Valles Marineris di Mars. Source: Data NASA",
        "link_text": "Valles Marineris: Grand Canyon of Mars. Source: Data NASA",
        "link_url": "https://www.nasa.gov/image-article/valles-marineris-grand-canyon-of-mars/",
        "facts": ["Panjang Valles Marineris: ~3.000-4.000 km", "bisa mencakup seperempat keliling Mars", "tempat destinasi wisata umat manusia berikutnya"],
        "text": """Jika Anda menganggap Grand Canyon itu besar, Valles Marineris akan membuat Anda terdiam. Ini bukan sekadar ngarai; ini adalah luka raksasa di wajah Mars, sebuah retakan tektonik yang membentang sepanjang benua Amerika Serikat. Berdiri di tepinya, Anda tidak akan melihat sisi seberang, hanya cakrawala yang jatuh ke kedalaman yang tak terukur.

Terbentuk bukan oleh air sungai seperti di Bumi, tetapi oleh planet itu sendiri yang meregang dan robek saat kerak Mars mendingin. Dinding-dindingnya menjulang setinggi 7 kilometer, menyimpan lapisan sejarah geologis yang lebih tua dari kehidupan apa pun yang kita kenal. Ini adalah arsip batu yang menunggu untuk dibaca.

Suatu hari nanti, manusia akan berdiri di sini, memandang kabut pagi yang mengisi lembah raksasa ini. Valles Marineris bukan hanya fitur geologis; ia adalah monumen keagungan alam semesta yang kasar dan tak kenal ampun, sebuah katedral alami di mana kita bisa merenungkan betapa kecilnya kita di hadapan kosmos."""
    },
    3: {
        "title": "FITUR GEOLOGIS RAKSASA \"OLYMPUS MONS\"",
        "img_file": "GunungTertinggiOlympusMons.png",
        "img_caption": "Gunung Tertinggi di Tata Surya Olympus Mons. Source: Data National Geographics",
        "link_text": "Mengenal Olympus Mons. Source: Data National Geographics",
        "link_url": "https://nationalgeographic.grid.id/read/133139693/mengenal-olympus-mons-gunung-berapi-tertinggi-di-tata-surya?page=all",
        "facts": ["tiga kali lebih tinggi dari Gunung Everest", "terbentuk karena ketiadaan lempeng tektonik di Mars", "next mountain untuk ditaklukkan"],
        "text": """Olympus Mons berdiri sebagai raja gunung di Tata Surya, sebuah titan yang menjulang menembus atmosfer tipis Mars. Dengan tinggi tiga kali Everest, puncaknya menyentuh kehampaan luar angkasa. Ini bukan sekadar gunung; ini adalah bukti kekuatan vulkanik yang tak tertandingi, tumbuh tanpa henti karena kerak Mars yang diam tak bergerak.

Mendaki Olympus Mons berarti berjalan keluar dari atmosfer planet. Dasarnya seluas negara Prancis, sebuah perisai raksasa yang dibangun dari aliran lava miliaran tahun lalu. Di puncaknya, kaldera raksasa menatap langit hitam berbintang, saksi bisu dari masa lalu Mars yang berapi-api dan penuh gejolak.

Bagi para penjelajah masa depan, menaklukkan Olympus Mons adalah cawan suci petualangan. Berdiri di puncaknya bukan hanya tentang memecahkan rekor ketinggian, tetapi tentang menyentuh batas langit itu sendiri, memandang lengkungan planet merah di bawah kaki, dan menyadari bahwa kita telah melangkah lebih jauh dari mimpi terliar leluhur kita."""
    },
    4: {
        "title": "ATMOSFER MARS \"100X LEBIH TIPIS DIBANDING BUMI\"",
        "img_file": "AtmosferTipislebihtipisdariBumi.png",
        "img_caption": "Perbedaan Atmosfer Mars & Bumi. Source: Data National Geographics",
        "link_text": "Dulu Mars memiliki atmosfer. Source: Data National Geographics",
        "link_url": "https://nationalgeographic.grid.id/read/13302142/dulu-planet-mars-memiliki-atmosfer-yang-sama-dengan-bumi",
        "facts": ["suhu ekstrem dan tidak memungkinkan air cair bertahan", "membuat Mars tidak layak huni saat ini", "masa lalu Mars lebih hangat dan lembab"],
        "text": """Atmosfer Mars adalah selimut tipis dan rapuh, sebuah sisa hantu dari masa lalu yang lebih tebal. Seratus kali lebih tipis dari Bumi dan didominasi karbon dioksida, ia tidak memberikan perlindungan dari dinginnya angkasa atau radiasi matahari yang ganas. Tanpa tekanan udara yang cukup, darah manusia akan mendidih seketika jika terpapar tanpa pelindung.

Namun, tipisnya atmosfer ini menceritakan kisah tragis tentang kehilangan. Miliaran tahun lalu, Mars memiliki langit biru dan awan tebal yang menaungi sungai-sungai mengalir. Hilangnya medan magnet membiarkan angin matahari mengikis atmosfer ini perlahan, mengubah surga basah menjadi gurun beku yang kita lihat hari ini.

Memahami atmosfer Mars adalah kunci untuk memahami nasib planet-planet. Ia mengajarkan kita betapa berharganya pelindung tak terlihat yang kita miliki di Bumi. Di Mars, setiap hembusan angin debu adalah pengingat akan kerapuhan sebuah dunia, dan tantangan terbesar yang harus kita atasi jika kita ingin menjadikan planet merah ini rumah kedua."""
    },
    5: {
        "title": "JEJAK KEHIDUPAN \"AIR ASIN & SEJARAHNYA\"",
        "img_file": "AirMemilikitudungeskutub.png",
        "img_caption": "Fosil Air di Planet Merah Karat. Source: Data CNBC",
        "link_text": "Ditemukan danau air asin di Mars. Source: Data CNBC",
        "link_url": "https://www.cnbcindonesia.com/tech/20200929121403-37-190232/ditemukan-danau-air-asin-di-mars-planet-merah-layak-huni",
        "facts": ["jejak kehidupan masa lalu atau sekarang", "membuat Mars bisa jadi layak huni saat ini", "prasyarat utama kehidupan seperti di Bumi"],
        "text": """Air adalah tanda tangan kehidupan, dan Mars menyembunyikannya dengan rapi. Di kutubnya yang membeku dan mungkin di danau-danau asin jauh di bawah permukaan, air masih bertahan. Ini bukan sekadar es; ini adalah kapsul waktu molekuler yang mungkin menyimpan mikroba purba yang tertidur, menunggu untuk ditemukan.

Penemuan air asin di Mars mengubah segalanya. Planet ini bukan mati, ia hanya tertidur. Keberadaan air cair, betapapun asin dan tersembunyinya, memberikan harapan bahwa kehidupan mungkin pernah—atau masih—ada di sana. Di mana ada air di Bumi, di situ ada kehidupan; prinsip ini mendorong kita untuk terus menggali pasir merah itu.

Bagi umat manusia, air ini adalah emas cair. Ia adalah sumber oksigen untuk bernapas dan bahan bakar roket untuk pulang. Menemukan dan memanen air di Mars bukan hanya tentang sains; ini adalah tentang kelangsungan hidup. Ini adalah langkah pertama untuk mengubah planet asing yang dingin menjadi tempat di mana anak cucu kita mungkin suatu hari nanti lahir."""
    },
    6: {
        "title": "MISTERI BATUAN \"CHEYAVA FALLS\"",
        "img_file": "biosignatureonMars.png",
        "img_caption": "Biosignature Mikrobial on Mars (tanda-tanda kehidupan). Source: Data NASA",
        "link_text": "Biosignature Mikrobial on Mars. Source: Data NASA",
        "link_url": "https://www.nasa.gov/news-release/nasa-says-mars-rover-discovered-potential-biosignature-last-year/",
        "facts": ["Penemuan tanda-tanda kehidupan", "Adanya jejak mikroba hidup di batuan Mars", "Kita tidak sendirian di alam semesta ini"],
        "text": """Di lembah sungai kuno Neretva Vallis, rover Perseverance menemukan sesuatu yang menakjubkan: batuan berbentuk panah bernama "Cheyava Falls". Batuan ini memiliki bercak-bercak putih dengan tepian hitam, persis seperti corak macan tutul. Struktur unik ini bukan sekadar hiasan alam, melainkan petunjuk terkuat yang pernah kita temukan tentang masa lalu Mars yang mungkin pernah menghuni kehidupan.

Mengapa ini begitu penting? Di Bumi, corak serupa terbentuk ketika mikroba purba mengubah batuan merah berkarat menjadi energi. Instrumen rover mendeteksi senyawa organik dan bukti aliran air di dalam batuan ini. Ini seperti menemukan 'sidik jari' kimiawi yang ditinggalkan oleh kehidupan mikroskopis miliaran tahun yang lalu, terkunci rapi di dalam batu merah itu.

Kita berdiri di ambang jawaban atas pertanyaan terbesar sepanjang masa: "Apakah kita sendirian?" Meski belum dikonfirmasi 100% sebagai alien, batuan ini adalah kapsul waktu yang menjanjikan. Kita sedang menatap jejak yang mungkin membuktikan bahwa alam semesta ini tidak sunyi, dan kehidupan, betapapun kecilnya, selalu mencari jalan untuk ada."""
    }
}

# Data struktur untuk konten Bumi (Point 1 - 6) - INDONESIA
EARTH_DETAILS_CONFIG_ID = {
    1: {
        "title": "PLANET BIRU EARTH",
        "img_file": "PlanetBiru.png",
        "img_caption": "Bumi: 71% permukaan tertutup air cair. Source: Data NASA",
        "link_text": "Kenapa Bumi Disebut Planet Biru? Source: Data NASA",
        "link_url": "https://rri.co.id/semarang/iptek/841328/kenapa-bumi-disebut-planet-biru",
        "facts": ["71% Tertutup Air", "97% adalah air laut asin yang tidak bisa langsung diminum", "tidak ada air = tidak ada kehidupan"],
        "text": """Bayangkan setitik debu biru yang melayang sendirian di hamparan kosmik yang gelap gulita. Itulah Bumi, satu-satunya rumah yang kita kenal. Warna birunya bukan sekadar hiasan, melainkan sinyal kehidupan—air cair yang menutupi sebagian besar permukaannya. Seperti kata Carl Sagan, dari kejauhan, Bumi tidak menunjukkan batas negara atau konflik ideologi, hanya sebuah kelereng biru yang rapuh dan indah.

Samudra di Bumi adalah jantung dari sistem iklim planet ini. Ia menyimpan panas matahari, mendistribusikannya ke seluruh dunia, dan menjadi rumah bagi jutaan spesies yang bahkan belum semuanya kita kenal. Air adalah pelarut universal kehidupan, medium di mana reaksi kimia kompleks pertama kali memicu percikan evolusi miliaran tahun yang lalu. Tanpa samudra yang luas ini, Bumi hanyalah batu kering dan mati seperti tetangganya.

Namun, kelimpahan ini menipu. Sebagian besar air itu asin dan tak bisa diminum. Kita hidup di tepi oasis yang rapuh, bergantung sepenuhnya pada siklus hidrologi yang menjaga air tawar tetap mengalir. Menjaga warna biru Bumi bukan hanya tentang estetika planet; ini adalah tentang memastikan kelangsungan satu-satunya biosfer yang mampu menopang kita di alam semesta yang luas ini."""
    },
    2: {
        "title": "PENGATUR BUMI \"LEMPENG TEKTONIK\"",
        "img_file": "LempengTektonikBumi.png",
        "img_caption": "Satu-satunya planet dengan tektonik aktif. Source: Data UMSU",
        "link_text": "Mengenal Lebih Dekat Planet Bumi. Source: Data UMSU",
        "link_url": "https://oif.umsu.ac.id/mengenal-lebih-dekat-planet-bumi/",
        "facts": ["Penyebab Gempa dan Gunung Berapi", "Bergerak sekitar 3 hingga 5 cm per tahun", "tanpa lempeng tektonik maka tidak ada iklim"],
        "text": """Bumi adalah planet yang hidup, bukan hanya di permukaannya, tetapi juga jauh di dalam perutnya. Lempeng tektonik adalah mesin raksasa yang terus bergerak, mendaur ulang kerak planet ini dalam siklus jutaan tahun. Pergerakan ini mungkin tampak menakutkan karena gempa dan gunung berapi yang ditimbulkannya, tetapi tanpa kekacauan geologis ini, kehidupan mungkin tidak akan bertahan.

Tektonik lempeng memainkan peran krusial dalam termostat planet. Melalui siklus karbon silikat, proses ini mengatur jumlah karbon dioksida di atmosfer, mencegah Bumi menjadi terlalu panas seperti Venus atau terlalu dingin seperti Mars. Ini adalah sistem daur ulang planet yang memastikan elemen-elemen penting terus tersedia bagi biosfer, menjaga keseimbangan kimiawi atmosfer dan lautan.

Jadi, ketika kita merasakan tanah berguncang, itu adalah denyut nadi planet yang sedang bekerja. Gunung berapi yang meletus bukan hanya bencana, tetapi juga pembawa nutrisi dari kedalaman yang menyuburkan tanah. Kita berutang keberadaan iklim yang stabil ini pada lantai dansa raksasa di bawah kaki kita yang tidak pernah berhenti bergerak."""
    },
    3: {
        "title": "NAFAS BUMI \"ATMOSFER KEHIDUPAN\"",
        "img_file": "AtmosferBumi.png",
        "img_caption": "Atmosfer Bumi yang sempurna untuk kehidupan. Source: Data Wikipedia",
        "link_text": "Atmosfer Bumi. Source: Data Wikipedia",
        "link_url": "https://id.wikipedia.org/wiki/Atmosfer_Bumi",
        "facts": ["mencegah suhu ekstrem antara siang dan malam", "Perisai Pelindung dari radiasi UV", "Rasio 78:21 diciptakan Tuhan secara seimbang"],
        "text": """Atmosfer Bumi adalah selubung tipis yang memisahkan kita dari kehampaan ruang angkasa yang mematikan. Ini bukan sekadar udara untuk bernapas; ini adalah perisai, selimut, dan laboratorium kimia sekaligus. Dengan komposisi 78% nitrogen dan 21% oksigen, atmosfer ini adalah hasil karya kehidupan itu sendiri—tanaman dan mikroba purba yang mengubah langit beracun menjadi paru-paru yang bisa kita hirup.

Lapisan ini bekerja tanpa henti melindungi kita. Di siang hari, ia menghalau radiasi ultraviolet yang membakar; di malam hari, ia memerangkap panas agar kita tidak membeku. Tanpa efek rumah kaca alami ini, suhu rata-rata Bumi akan berada jauh di bawah titik beku. Atmosfer juga adalah panggung bagi cuaca, tarian awan dan hujan yang mendistribusikan air kehidupan ke seluruh benua.

Namun, keseimbangan ini sangatlah halus. Kita sedang belajar bahwa mengubah komposisi atmosfer, meski sedikit, dapat memicu perubahan iklim yang drastis. Menatap langit biru yang cerah seharusnya mengingatkan kita bahwa kita hidup di dalam gelembung pelindung yang rapuh. Menjaganya tetap bersih dan stabil adalah satu-satunya cara memastikan 'nafas' Bumi ini terus menghidupi generasi mendatang."""
    },
    4: {
        "title": "PENJAGA BUMI \"PLANET ABU-ABU\"",
        "img_file": "BulanBumi.png",
        "img_caption": "Bulannya Bumi. Source: Data Kompas",
        "link_text": "Manfaat Bulan sebagai Satelit Bumi. Source: Data Kompas",
        "link_url": "https://www.kompas.com/skola/read/2020/07/18/170000869/manfaat-bulan-sebagai-satelit-bumi#:~:text=Tanpa%20Bulan%2C%20Bumi%20mungkin%20memiliki,saat%20ini%20mungkin%20akan%20punah.",
        "facts": ["gaya gravitasi Bulan mencegah poros Bumi berayun terlalu ekstrem", "kemiringan poros yang stabil menciptakan iklim yang relatif stabil", "tanpa Bulan maka air laut akan terangkat ke udara"],
        "text": """Bulan lebih dari sekadar lentera di malam hari; ia adalah jangkar gravitasi bagi Bumi. Tanpa satelit raksasa ini, poros rotasi Bumi akan berayun liar seperti gasing yang mau berhenti, menyebabkan perubahan iklim yang ekstrem dan kacau yang mungkin mencegah kehidupan kompleks berkembang. Bulan memegang Bumi dengan lembut, menjaga kemiringan poros kita stabil untuk menciptakan musim-musim yang teratur.

Tarian gravitasi antara Bumi dan Bulan juga menciptakan pasang surut lautan. Zona pasang surut ini diyakini oleh banyak ilmuwan sebagai tempat di mana kehidupan purba pertama kali belajar untuk beralih dari lautan ke daratan. Bulan telah menjadi bidan bagi evolusi, menarik kehidupan keluar dari air dan mendorongnya untuk menaklukkan benua.

Menatap Bulan purnama adalah menatap pelindung diam kita. Ia penuh dengan kawah, menanggung hantaman asteroid yang mungkin seharusnya mengenai Bumi. Hubungan kita dengan Bulan adalah ikatan kosmik yang mendalam; ia adalah pasangan dansa Bumi yang setia, menjaga irama kehidupan di planet ini tetap stabil selama miliaran tahun."""
    },
    5: {
        "title": "PELINDUNG TAK TERLIHAT \"MAGNETOSFER\"",
        "img_file": "MedanMagnetBumi.png",
        "img_caption": "Medan magnet melindungi dari angin matahari berbahaya. Source: Data GreenLab",
        "link_text": "Dampak Medan Magnet pada Lingkungan. Source: Data GreenLab",
        "link_url": "https://greenlab.co.id/news/dampak-medan-magnet-pada-lingkungan",
        "facts": ["mencegah atmosfer terkikis", "menjaga radiasi berbahaya tetap di luar jangkauan", "pembuat fenomena aurora di kutub"],
        "text": """Jauh di dalam inti Bumi, logam cair yang berputar menciptakan perisai tak terlihat yang membentang ribuan kilometer ke angkasa: Magnetosfer. Ini adalah medan gaya pelindung yang menangkis angin matahari—aliran partikel bermuatan mematikan yang terus-menerus ditembakkan oleh bintang kita. Tanpa perisai ini, atmosfer Bumi akan terkikis habis ke angkasa, nasib tragis yang dialami Mars.

Kita jarang menyadari keberadaannya, kecuali saat ia menampilkan dirinya dalam cahaya Aurora yang memukau di kutub. Cahaya menari itu adalah bukti visual dari pertempuran sengit yang terjadi di atas sana, di mana medan magnet kita membanting partikel berbahaya menjauh dari biosfer. Ini adalah sistem pertahanan planet yang aktif 24 jam sehari, melindungi DNA setiap makhluk hidup dari kerusakan radiasi.

Magnetosfer mengajarkan kita bahwa perlindungan terpenting seringkali tak terlihat oleh mata. Inti bumi yang dinamo ini adalah alasan mengapa kita masih memiliki air dan udara. Kehidupan di permukaan yang tenang ini dimungkinkan oleh gejolak inferno logam cair di pusat planet. Kita hidup aman di dalam kepompong magnetik yang ajaib."""
    },
    6: {
        "title": "KEHIDUPAN DI DALAM DEBU KOSMIK \"BUMI\"",
        "img_file": "KehidupanBumi.png",
        "img_caption": "Salah satu penduduk Bumi \"Fauna\". Source: Data National Geographics",
        "link_text": "Bumi Satu-Satunya Planet Pendukung Kehidupan. Source: Data National Geographic",
        "link_url": "https://nationalgeographic.grid.id/read/13304122/bumi-satu-satunya-planet-pendukung-kehidupan",
        "facts": ["Jarak yang tepat dari Matahari", "NASA dalam misi pencarian mencari Bumi ke-2", "Mars bisa menjadi Bumi ke-2 dengan cara mengterraforming Planet Merah itu"],
        "text": """Dari semua keajaiban di Tata Surya, tidak ada yang lebih membingungkan dan indah daripada kehidupan di Bumi. Di sinilah materi alam semesta menjadi sadar akan dirinya sendiri. Bumi bukan hanya batu basah; ia adalah super-organisme yang kompleks, di mana geologi, atmosfer, dan biologi saling terkait dalam simfoni yang rumit. Kita berada di zona 'Goldilocks', tidak terlalu panas, tidak terlalu dingin, tepat untuk air cair dan kimia kehidupan.

Keberadaan kita adalah hasil dari serangkaian kebetulan yang nyaris mustahil. Dari posisi di galaksi, kestabilan matahari, hingga perlindungan Jupiter dan Bulan, semuanya berkonspirasi untuk memungkinkan kita ada di sini. NASA dan ilmuwan terus mencari 'Bumi kedua' di luar sana, tetapi sejauh ini, kesunyian adalah satu-satunya jawaban. Ini membuat planet kita semakin berharga.

Mars mungkin adalah masa depan, tapi Bumi adalah tempat kita berasal. Memahami betapa istimewanya kehidupan di sini seharusnya memicu rasa tanggung jawab yang mendalam. Kita adalah penjaga satu-satunya nyala api kesadaran yang kita ketahui di alam semesta yang luas dan dingin ini. Menjaga Bumi bukan pilihan; itu adalah imperatif eksistensial bagi kelangsungan kisah kita di antara bintang-bintang."""
    }
}

# Data struktur untuk konten Mars (Point 1 - 6) - ENGLISH
MARS_DETAILS_CONFIG_EN = {
    1: {
        "title": "RED PLANET MARS",
        "img_file": "permukaanmerahMars.png",
        "img_caption": "Red Color is caused by iron oxide (rust) dust covering its surface. Source: Data NASA",
        "link_text": "Red Color caused by rust. Source: Data NASA",
        "link_url": "https://science.nasa.gov/mars/facts/",
        "facts": ["Mars is red", "Covered by iron oxide dust (rust)", "Distinctive color clearly visible from Earth"],
        "text": """Imagine a world where rusting iron is not a sign of decay, but the primer paint for an entire planet. Mars is red not because of heat, but because of oxidation—a giant chemical process occurring over billions of years, turning iron rocks into fine blood-red dust that coats everything.

The wind on Mars never stops working. It lifts these rust dust particles into the atmosphere, creating pink skies during the day and haunting blue twilights. This is the universe's chemical laboratory showcasing the beauty of a simple reaction between iron and ancient oxygen remains.

Gazing at Mars in the night sky is gazing at frozen geological history. Its red color is both a warning and an invitation; it tells the story of a planet that might have once been blue like Earth, before slowly drying out and rusting, leaving an eternal monument to time and change."""
    },
    2: {
        "title": "GIANT CANYON \"VALLES MARINERIS\"",
        "img_file": "NgaraiRaksasaVallesMarineris.png",
        "img_caption": "Valles Marineris: Grand Canyon of Mars. Source: Data NASA",
        "link_text": "Valles Marineris: Grand Canyon of Mars. Source: Data NASA",
        "link_url": "https://www.nasa.gov/image-article/valles-marineris-grand-canyon-of-mars/",
        "facts": ["Length of Valles Marineris: ~3,000-4,000 km", "Could span a quarter of Mars' circumference", "Next tourist destination for humanity"],
        "text": """If you think the Grand Canyon is big, Valles Marineris will leave you speechless. This is not just a canyon; it is a giant scar on the face of Mars, a tectonic crack stretching the length of the continental United States. Standing on its edge, you wouldn't see the other side, only the horizon falling into immeasurable depths.

Formed not by river water like on Earth, but by the planet itself stretching and tearing as the Martian crust cooled. Its walls rise 7 kilometers high, holding layers of geological history older than any life we know. It is a stone archive waiting to be read.

One day, humans will stand here, watching the morning mist fill this giant valley. Valles Marineris is not just a geological feature; it is a monument to the rough and unforgiving grandeur of the universe, a natural cathedral where we can reflect on how small we are in the face of the cosmos."""
    },
    3: {
        "title": "GIANT GEOLOGICAL FEATURE \"OLYMPUS MONS\"",
        "img_file": "GunungTertinggiOlympusMons.png",
        "img_caption": "Tallest Volcano in the Solar System Olympus Mons. Source: Data National Geographics",
        "link_text": "Mengenal Olympus Mons. Source: Data National Geographics",
        "link_url": "https://nationalgeographic.grid.id/read/133139693/mengenal-olympus-mons-gunung-berapi-tertinggi-di-tata-surya?page=all",
        "facts": ["Three times higher than Mount Everest", "Formed due to lack of tectonic plates on Mars", "Next mountain to conquer"],
        "text": """Olympus Mons stands as the king of mountains in the Solar System, a titan rising through the thin Martian atmosphere. With a height three times that of Everest, its peak touches the vacuum of space. This is not just a mountain; it is proof of unparalleled volcanic power, growing endlessly because the Martian crust stands still.

Climbing Olympus Mons means walking out of the planet's atmosphere. Its base is as large as the country of France, a giant shield built from lava flows billions of years ago. At its summit, a giant caldera stares into the black starry sky, a silent witness to Mars' fiery and turbulent past.

For future explorers, conquering Olympus Mons is the holy grail of adventure. Standing at its peak is not just about breaking altitude records, but about touching the edge of the sky itself, gazing at the curvature of the red planet beneath one's feet, and realizing we have stepped further than our ancestors' wildest dreams."""
    },
    4: {
        "title": "MARS ATMOSPHERE \"100X THINNER THAN EARTH\"",
        "img_file": "AtmosferTipislebihtipisdariBumi.png",
        "img_caption": "Difference between Mars & Earth Atmosphere. Source: Data National Geographics",
        "link_text": "Dulu Mars memiliki atmosfer. Source: Data National Geographics",
        "link_url": "https://nationalgeographic.grid.id/read/13302142/dulu-planet-mars-memiliki-atmosfer-yang-sama-dengan-bumi",
        "facts": ["Extreme temperatures and does not allow liquid water to persist", "Makes Mars uninhabitable today", "Mars' past was warmer and wetter"],
        "text": """The atmosphere of Mars is a thin and fragile blanket, a ghostly remnant of a thicker past. One hundred times thinner than Earth's and dominated by carbon dioxide, it provides no protection from the cold of space or fierce solar radiation. Without sufficient air pressure, human blood would boil instantly if exposed without protection.

However, the thinness of this atmosphere tells a tragic story of loss. Billions of years ago, Mars had blue skies and thick clouds shading flowing rivers. The loss of its magnetic field let the solar wind erode this atmosphere slowly, turning a wet paradise into the frozen desert we see today.

Understanding Mars' atmosphere is key to understanding the fate of planets. It teaches us how precious the invisible shield we have on Earth is. On Mars, every gust of dusty wind is a reminder of a world's fragility, and the greatest challenge we must overcome if we want to make this red planet a second home."""
    },
    5: {
        "title": "TRACES OF LIFE \"SALTY WATER & HISTORY\"",
        "img_file": "AirMemilikitudungeskutub.png",
        "img_caption": "Water Fossils on the Rusty Red Planet. Source: Data CNBC",
        "link_text": "Ditemukan danau air asin di Mars. Source: Data CNBC",
        "link_url": "https://www.cnbcindonesia.com/tech/20200929121403-37-190232/ditemukan-danau-air-asin-di-mars-planet-merah-layak-huni",
        "facts": ["Traces of past or present life", "Makes Mars potentially habitable today", "Main prerequisite for life like on Earth"],
        "text": """Water is the signature of life, and Mars hides it neatly. In its frozen poles and perhaps in salty lakes deep beneath the surface, water still persists. This is not just ice; it is a molecular time capsule that might hold ancient dormant microbes, waiting to be found.

The discovery of salty water on Mars changed everything. The planet is not dead, only sleeping. The existence of liquid water, however salty and hidden, gives hope that life might have once—or still—exists there. Where there is water on Earth, there is life; this principle drives us to keep digging into that red sand.

For humanity, this water is liquid gold. It is a source of oxygen to breathe and rocket fuel to return home. Finding and harvesting water on Mars is not just about science; it is about survival. It is the first step to turning a cold alien planet into a place where our descendants might one day be born."""
    },
    6: {
        "title": "ROCK MYSTERY \"CHEYAVA FALLS\"",
        "img_file": "biosignatureonMars.png",
        "img_caption": "Microbial Biosignature on Mars (signs of life). Source: Data NASA",
        "link_text": "Biosignature Mikrobial on Mars. Source: Data NASA",
        "link_url": "https://www.nasa.gov/news-release/nasa-says-mars-rover-discovered-potential-biosignature-last-year/",
        "facts": ["Discovery of signs of life", "Presence of microbial traces in Martian rocks", "We are not alone in this universe"],
        "text": """In the ancient river valley of Neretva Vallis, the Perseverance rover found something amazing: an arrowhead-shaped rock named 'Cheyava Falls'. This rock has white spots with black edges, exactly like leopard spots. This unique structure is not just nature's decoration, but the strongest clue we have ever found about Mars' past that might have hosted life.

Why is this so important? On Earth, similar patterns form when ancient microbes convert rusty red rock into energy. Rover instruments detected organic compounds and evidence of water flow within this rock. It's like finding a chemical 'fingerprint' left by microscopic life billions of years ago, locked neatly inside that red stone.

We stand on the brink of the answer to the greatest question of all time: 'Are we alone?' Although not yet confirmed 100% as alien, this rock is a promising time capsule. We are staring at a trace that might prove this universe is not silent, and life, however small, always finds a way to exist."""
    }
}

# Data struktur untuk konten Bumi (Point 1 - 6) - ENGLISH
EARTH_DETAILS_CONFIG_EN = {
    1: {
        "title": "BLUE PLANET EARTH",
        "img_file": "PlanetBiru.png",
        "img_caption": "Earth: 71% surface covered by liquid water. Source: Data NASA",
        "link_text": "Kenapa Bumi Disebut Planet Biru? Source: Data NASA",
        "link_url": "https://rri.co.id/semarang/iptek/841328/kenapa-bumi-disebut-planet-biru",
        "facts": ["71% Covered in Water", "97% is salty seawater that cannot be drunk directly", "No water = no life"],
        "text": """Imagine a speck of blue dust floating alone in the pitch-black cosmic expanse. That is Earth, the only home we know. Its blue color is not just decoration, but a signal of life—liquid water covering most of its surface. As Carl Sagan said, from a distance, Earth shows no national borders or ideological conflicts, only a fragile and beautiful blue marble.

The ocean on Earth is the heart of the planet's climate system. It stores solar heat, distributes it around the world, and is home to millions of species we haven't even fully identified. Water is the universal solvent of life, the medium where complex chemical reactions first sparked the spark of evolution billions of years ago. Without this vast ocean, Earth would be just a dry and dead rock like its neighbors.

However, this abundance is deceptive. Most of that water is salty and undrinkable. We live on the edge of a fragile oasis, depending entirely on the hydrological cycle that keeps fresh water flowing. Preserving Earth's blue color is not just about planetary aesthetics; it is about ensuring the survival of the only biosphere capable of sustaining us in this vast universe."""
    },
    2: {
        "title": "EARTH REGULATOR \"TECTONIC PLATES\"",
        "img_file": "LempengTektonikBumi.png",
        "img_caption": "The only planet with active tectonics. Source: Data UMSU",
        "link_text": "Mengenal Lebih Dekat Planet Bumi. Source: Data UMSU",
        "link_url": "https://oif.umsu.ac.id/mengenal-lebih-dekat-planet-bumi/",
        "facts": ["Cause of Earthquakes and Volcanoes", "Moves about 3 to 5 cm per year", "Without tectonic plates, there is no climate"],
        "text": """Earth is a living planet, not just on its surface, but also deep within its belly. Tectonic plates are giant engines that keep moving, recycling the planet's crust in a cycle of millions of years. This movement might seem terrifying because of the earthquakes and volcanoes it causes, but without this geological chaos, life might not survive.

Plate tectonics plays a crucial role in the planet's thermostat. Through the carbonate-silicate cycle, this process regulates the amount of carbon dioxide in the atmosphere, preventing Earth from becoming too hot like Venus or too cold like Mars. It is a planetary recycling system that ensures essential elements remain available to the biosphere, maintaining the chemical balance of the atmosphere and oceans.

So, when we feel the ground shake, it is the pulse of the planet at work. An erupting volcano is not just a disaster, but also a carrier of nutrients from the depths that fertilize the soil. We owe the existence of this stable climate to the giant dance floor beneath our feet that never stops moving."""
    },
    3: {
        "title": "BREATH OF EARTH \"ATMOSPHERE OF LIFE\"",
        "img_file": "AtmosferBumi.png",
        "img_caption": "Earth's Atmosphere perfect for life. Source: Data Wikipedia",
        "link_text": "Atmosfer Bumi. Source: Data Wikipedia",
        "link_url": "https://id.wikipedia.org/wiki/Atmosfer_Bumi",
        "facts": ["Prevents extreme temperatures between day and night", "Protective Shield from UV radiation", "Ratio 78:21 created by God in balance"],
        "text": """Earth's atmosphere is a thin veil separating us from the deadly void of space. It is not just air to breathe; it is a shield, a blanket, and a chemical laboratory all at once. With a composition of 78% nitrogen and 21% oxygen, this atmosphere is the masterpiece of life itself—ancient plants and microbes that turned a toxic sky into lungs we can inhale.

This layer works tirelessly to protect us. During the day, it blocks burning ultraviolet radiation; at night, it traps heat so we don't freeze. Without this natural greenhouse effect, Earth's average temperature would be far below freezing. The atmosphere is also the stage for weather, the dance of clouds and rain distributing the water of life across continents.

However, this balance is extremely delicate. We are learning that altering the atmosphere's composition, even slightly, can trigger drastic climate change. Gazing at a clear blue sky should remind us that we live inside a fragile protective bubble. Keeping it clean and stable is the only way to ensure this 'breath' of Earth continues to sustain future generations."""
    },
    4: {
        "title": "EARTH'S GUARDIAN \"THE GREY PLANET\"",
        "img_file": "BulanBumi.png",
        "img_caption": "Earth's Moon. Source: Data Kompas",
        "link_text": "Manfaat Bulan sebagai Satelit Bumi. Source: Data Kompas",
        "link_url": "https://www.kompas.com/skola/read/2020/07/18/170000869/manfaat-bulan-sebagai-satelit-bumi#:~:text=Tanpa%20Bulan%2C%20Bumi%20mungkin%20memiliki,saat%20ini%20mungkin%20akan%20punah.",
        "facts": ["Moon's gravity prevents Earth's axis from swinging too wildly", "Stable axial tilt creates relatively stable climate", "Without the Moon, sea water would be lifted into the air"],
        "text": """The Moon is more than just a lantern in the night; it is a gravitational anchor for Earth. Without this giant satellite, Earth's rotational axis would swing wildly like a wobbling top, causing extreme and chaotic climate changes that might prevent complex life from developing. The Moon holds Earth gently, keeping our axial tilt stable to create regular seasons.

The gravitational dance between Earth and Moon also creates ocean tides. This intertidal zone is believed by many scientists to be the place where ancient life first learned to transition from the ocean to land. The Moon has been a midwife to evolution, pulling life out of the water and encouraging it to conquer the continents.

Gazing at the full Moon is gazing at our silent guardian. It is full of craters, bearing the brunt of asteroid impacts that might have otherwise hit Earth. Our relationship with the Moon is a deep cosmic bond; it is Earth's faithful dance partner, keeping the rhythm of life on this planet stable for billions of years."""
    },
    5: {
        "title": "INVISIBLE PROTECTOR \"MAGNETOSPHERE\"",
        "img_file": "MedanMagnetBumi.png",
        "img_caption": "Magnetic field protects from dangerous solar wind. Source: Data GreenLab",
        "link_text": "Dampak Medan Magnet pada Lingkungan. Source: Data GreenLab",
        "link_url": "https://greenlab.co.id/news/dampak-medan-magnet-pada-lingkungan",
        "facts": ["Prevents atmosphere from being stripped away", "Keeps harmful radiation out of reach", "Creator of aurora phenomena at the poles"],
        "text": """Deep within Earth's core, swirling molten metal creates an invisible shield stretching thousands of kilometers into space: the Magnetosphere. This is a protective force field that deflects the solar wind—a stream of deadly charged particles constantly fired by our star. Without this shield, Earth's atmosphere would be stripped away into space, a tragic fate suffered by Mars.

We rarely notice its existence, except when it reveals itself in the mesmerizing Aurora lights at the poles. Those dancing lights are visual proof of the fierce battle happening up there, where our magnetic field slams dangerous particles away from the biosphere. It is a planetary defense system active 24 hours a day, protecting the DNA of every living thing from radiation damage.

The magnetosphere teaches us that the most important protection is often invisible to the eye. This dynamo core is the reason we still have water and air. Life on this calm surface is made possible by the turbulent inferno of molten metal at the planet's center. We live safely inside a magical magnetic cocoon."""
    },
    6: {
        "title": "LIFE IN COSMIC DUST \"EARTH\"",
        "img_file": "KehidupanBumi.png",
        "img_caption": "One of Earth's residents \"Fauna\". Source: Data National Geographics",
        "link_text": "Bumi Satu-Satunya Planet Pendukung Kehidupan. Source: Data National Geographic",
        "link_url": "https://nationalgeographic.grid.id/read/13304122/bumi-satu-satunya-planet-pendukung-kehidupan",
        "facts": ["Right distance from the Sun", "NASA on a mission to find a 2nd Earth", "Mars could become a 2nd Earth by terraforming"],
        "text": """Of all the wonders in the Solar System, none is more baffling and beautiful than life on Earth. Here, the matter of the universe became aware of itself. Earth is not just a wet rock; it is a complex super-organism, where geology, atmosphere, and biology are intertwined in an intricate symphony. We are in the 'Goldilocks' zone, not too hot, not too cold, just right for liquid water and the chemistry of life.

Our existence is the result of a series of almost impossible coincidences. From position in the galaxy, solar stability, to the protection of Jupiter and the Moon, everything conspired to allow us to be here. NASA and scientists continue to search for a 'second Earth' out there, but so far, silence is the only answer. This makes our planet even more precious.

Mars might be the future, but Earth is where we come from. Understanding how special life is here should trigger a deep sense of responsibility. We are the guardians of the only flame of consciousness we know of in this vast and cold universe. Protecting Earth is not a choice; it is an existential imperative for the continuation of our story among the stars."""
    }
}

PLANET_DETAILS_DATA = {
    # Nanti di-load dinamis berdasarkan CURRENT_LANG,
    # tapi agar code lama aman, kita map defaultnya ke ID dulu atau logic di Modal
}

def load_planet_detail_image(filename):
    """Load gambar untuk modal Planet Detail berdasarkan nama file"""
    path = os.path.join(os.path.dirname(__file__), filename)
    try:
        img = pygame.image.load(path).convert_alpha()
        return img
    except Exception as e:
        log(f"Gagal load {filename}: {e}")
        # Fallback placeholder jika gambar tidak ditemukan
        s = pygame.Surface((400, 300))
        s.fill((50, 0, 0))
        font = pygame.font.SysFont("arial", 20)
        txt = font.render(f"Img Not Found: {filename}", True, (255, 255, 255))
        s.blit(txt, txt.get_rect(center=s.get_rect().center))
        return s

# Mengganti MarsBiosignatureModal dengan MarsUniversalModal yang fleksibel
class PlanetUniversalModal:
    def __init__(self, font, planet_name="Mars", config_id=6):
        self.font = font
        
        # Select dictionary based on planet name and language
        config_map = {}
        if planet_name == "Mars":
            config_map = MARS_DETAILS_CONFIG_ID if CURRENT_LANG == "id" else MARS_DETAILS_CONFIG_EN
        elif planet_name == "Earth":
            config_map = EARTH_DETAILS_CONFIG_ID if CURRENT_LANG == "id" else EARTH_DETAILS_CONFIG_EN
            
        self.config = config_map.get(config_id, config_map.get(6, {}))
        
        # Fallback safety
        if not self.config: 
            self.config = MARS_DETAILS_CONFIG_ID[6]
            
        self.title_font = pygame.font.SysFont("arial", 28, bold=True)
        self.body_font = pygame.font.SysFont("georgia", 18) 
        self.bold_font = pygame.font.SysFont("georgia", 18, bold=True)
        self.fact_font = pygame.font.SysFont("arial", 14, bold=True)
        self.link_font = pygame.font.SysFont("arial", 12)
        self.caption_font = pygame.font.SysFont("arial", 14, italic=True)
        self.blur = BlurLayer()
        
        self.image = load_planet_detail_image(self.config["img_file"])
        self.panel = None
        self.panel_rect = None
        self.close_rect = None
        
        self.scroll_y = 0
        self.scroll_x = 0
        self.max_scroll_y = 0
        self.max_scroll_x = 0
        
        self.view_rect = None # Area viewport
        self.content_surf = None # Surface konten keseluruhan
        
        self.link_rect_rel = None # Rect untuk link (relatif thd content_surf)
        self.link_hover = False
        
        self.pad = 30
        self.mars_red = (188, 39, 50)
        
    def open(self, background):
        self.blur.from_surface(background)
        self.build()

    def build(self):
        w = min(1000, WIDTH - 60)
        h = min(800, HEIGHT - 60)
        
        self.panel = pygame.Surface((w, h), pygame.SRCALPHA)
        self.panel.fill((20, 20, 25, 245)) # Gelap elegan
        pygame.draw.rect(self.panel, self.mars_red, self.panel.get_rect(), 2, border_radius=12)
        
        # 1. Judul (Statis di panel)
        title_str = self.config["title"]
        title = self.title_font.render(title_str, True, (255, 200, 200))
        self.panel.blit(title, title.get_rect(midtop=(w/2, self.pad)))
        
        view_start_y = self.pad + title.get_height() + 20
        view_h = h - view_start_y - self.pad
        self.view_rect = pygame.Rect(self.pad, view_start_y, w - self.pad*2, view_h)
        
        # --- MENYUSUN KONTEN ---
        # Gambar
        img_w, img_h = self.image.get_size()
        
        # Scaling gambar agar "sedang"
        target_img_h = 280
        scale = target_img_h / img_h
        img_w = int(img_w * scale)
        img_h = int(target_img_h)
        scaled_img = pygame.transform.smoothscale(self.image, (img_w, img_h))
        
        # Area Panah & Fakta (Kanan Gambar)
        fact_area_w = 300 
        
        # Total lebar bagian atas
        top_section_w = img_w + 20 + fact_area_w
        
        # Text Content Wrapper
        text_wrap_w = max(self.view_rect.width, 600)
        
        # Total Surface Width
        total_content_w = max(top_section_w, text_wrap_w)
        
        # Render Text Lines
        wrapper = textwrap.TextWrapper(width=int(text_wrap_w / 9)) 
        paragraphs = self.config["text"].split('\n\n')
        text_surfaces = []
        for para in paragraphs:
            lines = wrapper.wrap(para)
            for line in lines:
                s = self.body_font.render(line, True, (230, 230, 230))
                text_surfaces.append(s)
            text_surfaces.append(None) # Spacer
            
        # Hitung Tinggi Total
        text_h = 0
        for s in text_surfaces:
            if s: text_h += s.get_height() + 5
            else: text_h += 15
            
        # Judul keterangan gambar / Link
        caption_str = self.config["img_caption"] # Using caption as the link text usually
        link_surf = self.link_font.render(caption_str, True, (200, 200, 255))
        
        total_h = img_h + 30 + link_surf.get_height() + 20 + text_h + 20
        
        self.content_surf = pygame.Surface((total_content_w, total_h), pygame.SRCALPHA)
        
        # --- GAMBAR KE SURFACE ---
        curr_y = 0
        
        # 1. Gambar
        self.content_surf.blit(scaled_img, (0, curr_y))
        
        # 2. Panah & Fakta
        arrow_start_x = img_w + 10
        arrow_center_y = curr_y + img_h // 2
        facts = self.config["facts"]
        
        # Adjust vertical spread of facts
        fact_y_start = arrow_center_y - 60
        
        for i, fact in enumerate(facts):
            fy = fact_y_start + i * 60
            p_end = (arrow_start_x - 5, fy)
            p_start = (arrow_start_x + 30, fy)
            pygame.draw.line(self.content_surf, (255, 50, 50), p_start, p_end, 3)
            pygame.draw.polygon(self.content_surf, (255, 50, 50), [
                p_end, (p_end[0] + 10, p_end[1] - 5), (p_end[0] + 10, p_end[1] + 5)
            ])
            # Render fact text multi-line if needed (simple wrap)
            f_lines = textwrap.wrap(fact, width=35)
            line_h_fact = self.fact_font.get_linesize()
            total_fact_h = len(f_lines) * line_h_fact
            fact_curr_y = fy - total_fact_h // 2
            
            for f_line in f_lines:
                f_surf = self.fact_font.render(f_line, True, (255, 255, 255))
                self.content_surf.blit(f_surf, (arrow_start_x + 40, fact_curr_y))
                fact_curr_y += line_h_fact

        curr_y += img_h + 10
        
        # 3. Link / Caption
        self.link_rect_rel = link_surf.get_rect(topleft=(0, curr_y))
        self.content_surf.blit(link_surf, self.link_rect_rel)
        curr_y += link_surf.get_height() + 20
        
        # 4. Text
        for s in text_surfaces:
            if s:
                self.content_surf.blit(s, (0, curr_y))
                curr_y += s.get_height() + 5
            else:
                curr_y += 15
                
        # Scroll logic
        self.max_scroll_y = max(0, total_h - view_h)
        self.max_scroll_x = max(0, total_content_w - self.view_rect.width)
        
        # Close button
        self.close_rect = pygame.Rect(w - 40, 10, 30, 30)
        pygame.draw.rect(self.panel, (200, 50, 50), self.close_rect, border_radius=5)
        x_char = self.title_font.render("X", True, (255, 255, 255))
        self.panel.blit(x_char, x_char.get_rect(center=self.close_rect.center))
        
        self.panel_rect = self.panel.get_rect(center=(WIDTH/2, HEIGHT/2))

    def draw(self, surface):
        self.blur.draw(surface) # Draw blurred background
        
        # Blit Panel Base
        surface.blit(self.panel, self.panel_rect)
        
        # Clipping & Content Rendering
        screen_view_rect = self.view_rect.move(self.panel_rect.topleft)
        surface.set_clip(screen_view_rect)
        
        # Posisi konten berdasarkan scroll
        content_pos = (screen_view_rect.x - self.scroll_x, screen_view_rect.y - self.scroll_y)
        surface.blit(self.content_surf, content_pos)
        
        # Animasi Hover Link (Digambar ulang jika hover agar terlihat 'aktif')
        if self.link_hover:
            # Hitung posisi absolut link di layar
            link_abs_x = content_pos[0] + self.link_rect_rel.x
            link_abs_y = content_pos[1] + self.link_rect_rel.y
            
            # Cek apakah link terlihat di viewport
            link_rect_screen = pygame.Rect(link_abs_x, link_abs_y, self.link_rect_rel.width, self.link_rect_rel.height)
            if screen_view_rect.colliderect(link_rect_screen):
                # Highlight effect
                pygame.draw.line(surface, (255, 255, 255), link_rect_screen.bottomleft, link_rect_screen.bottomright, 1)

        surface.set_clip(None)
        
        # Scrollbars
        if self.max_scroll_y > 0:
            sb_w = 6
            sb_h = screen_view_rect.height
            sb_x = screen_view_rect.right + 5
            thumb_h = max(20, sb_h * (sb_h / self.content_surf.get_height()))
            scroll_ratio = self.scroll_y / self.max_scroll_y
            thumb_y = screen_view_rect.top + scroll_ratio * (sb_h - thumb_h)
            pygame.draw.rect(surface, (50, 50, 50), (sb_x, screen_view_rect.top, sb_w, sb_h), border_radius=3)
            pygame.draw.rect(surface, (150, 150, 150), (sb_x, thumb_y, sb_w, thumb_h), border_radius=3)
            
        if self.max_scroll_x > 0:
            sb_h = 6
            sb_w = screen_view_rect.width
            sb_y = screen_view_rect.bottom + 5
            thumb_w = max(20, sb_w * (sb_w / self.content_surf.get_width()))
            scroll_ratio = self.scroll_x / self.max_scroll_x
            thumb_x = screen_view_rect.left + scroll_ratio * (sb_w - thumb_w)
            pygame.draw.rect(surface, (50, 50, 50), (screen_view_rect.left, sb_y, sb_w, sb_h), border_radius=3)
            pygame.draw.rect(surface, (150, 150, 150), (thumb_x, sb_y, thumb_w, sb_h), border_radius=3)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "close"
            elif event.key == pygame.K_DOWN:
                self.scroll_y = min(self.scroll_y + 20, self.max_scroll_y)
            elif event.key == pygame.K_UP:
                self.scroll_y = max(self.scroll_y - 20, 0)
            elif event.key == pygame.K_RIGHT:
                self.scroll_x = min(self.scroll_x + 20, self.max_scroll_x)
            elif event.key == pygame.K_LEFT:
                self.scroll_x = max(self.scroll_x - 20, 0)
        elif event.type == pygame.MOUSEWHEEL:
            # Shift scroll for horizontal? Or just standard vertical
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
                 self.scroll_x = min(max(self.scroll_x - event.y * 30, 0), self.max_scroll_x)
            else:
                 self.scroll_y = min(max(self.scroll_y - event.y * 30, 0), self.max_scroll_y)
        elif event.type == pygame.MOUSEMOTION:
            # Check hover link
            screen_view_rect = self.view_rect.move(self.panel_rect.topleft)
            content_pos = (screen_view_rect.x - self.scroll_x, screen_view_rect.y - self.scroll_y)
            link_abs_rect = self.link_rect_rel.move(content_pos)
            
            # Hanya deteksi jika di dalam viewport
            if screen_view_rect.collidepoint(event.pos) and link_abs_rect.collidepoint(event.pos):
                self.link_hover = True
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
            else:
                if self.link_hover:
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
                self.link_hover = False
                
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                # Cek Link Click
                if self.link_hover:
                    open_url(self.config["link_url"])
                    return None

                close_abs = self.close_rect.move(self.panel_rect.topleft)
                if close_abs.collidepoint(event.pos):
                    return "close"
                if not self.panel_rect.collidepoint(event.pos):
                    return "close"
        return None

# ==============================================================================

class Camera2D:
    def __init__(self, pos=(0.0, 0.0), zoom=1.0, rot=0.0):
        self.pos = Vector2(pos)
        self._zoom_k = math.log(max(ZOOM_EPSILON, zoom))
        self.rot = float(rot)
        self.y_scale = VERTICAL_SCALE
        self.angle_mode = AngleMode.OBLIQUE_45
        self._update_cache()

    @property
    def zoom(self):
        return max(ZOOM_EPSILON, math.exp(self._zoom_k))

    def adjust_zoom(self, delta_k):
        self._zoom_k += delta_k
        log(f"zoom k={self._zoom_k:.3f} scale={self.zoom:.3e}")

    def set_angle_mode(self, mode: AngleMode):
        self.angle_mode = mode
        if mode is AngleMode.SIDE_0:
            self.y_scale = 0.0
        elif mode is AngleMode.TOP_90:
            self.y_scale = 1.0
        else:
            self.y_scale = 0.5
        log(f"angle preset {mode.name}")

    def _update_cache(self):
        self._cos = math.cos(self.rot)
        self._sin = math.sin(self.rot)

    def world_to_screen(self, world_xy, z=0.0):
        x, y = world_xy
        x -= self.pos.x
        y -= self.pos.y
        x_r = x * self._cos + y * self._sin
        y_r = -x * self._sin + y * self._cos
        y_r *= self.y_scale
        z_zoom = self.zoom
        x_r *= z_zoom
        y_r *= z_zoom
        y_r -= z * z_zoom
        y_r = -y_r
        return int(WIDTH / 2 + x_r), int(HEIGHT / 2 + y_r)

    def screen_to_world(self, screen_xy, z=0.0):
        x, y = screen_xy
        x -= WIDTH / 2
        y -= HEIGHT / 2
        y = -y
        z_zoom = self.zoom
        x /= z_zoom
        y = (y + z * z_zoom) / z_zoom
        if self.y_scale > ZOOM_EPSILON:
            y /= self.y_scale
        else:
            y = 0.0
        x_w = x * self._cos - y * self._sin
        y_w = x * self._sin + y * self._cos
        x_w += self.pos.x
        y_w += self.pos.y
        return Vector2(x_w, y_w)

class Planet:
    def __init__(self, name, color, orbit_radius, radius, period_days):
        self.name = name
        self.color = color
        self.orbit_radius = orbit_radius
        self.radius = radius
        self.period_days = period_days
        self.period_seconds = period_days / 10.0
        self.angular_velocity = 2 * math.pi / self.period_seconds
        self.angle = 0.0
        self.elapsed = 0.0
        self.body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.body.position = (orbit_radius, 0)

    def update(self, dt):
        self.angle = (self.angle + self.angular_velocity * dt) % (2 * math.pi)
        self.elapsed = (self.elapsed + dt) % self.period_seconds
        x = self.orbit_radius * math.cos(self.angle)
        y = self.orbit_radius * math.sin(self.angle)
        self.body.position = (x, y)
        return x, y

def draw_orbits(surface, planets, camera, sketch_mode=False):
    color = (50, 50, 50) if sketch_mode else None
    for p in planets:
        points = []
        for deg in range(0, 360, 2):
            rad = math.radians(deg)
            x = p.orbit_radius * math.cos(rad)
            y = p.orbit_radius * math.sin(rad)
            points.append(camera.world_to_screen((x, y)))
        
        orbit_color = color if sketch_mode else p.color
        pygame.draw.aalines(surface, orbit_color, True, points, 1)

_well_cache = None

def draw_curvature(surface, camera, sketch_mode=False):
    if not SHOW_WELL:
        return
    global _well_cache
    outer = OUTER_ORBIT_RADIUS
    extent = int(outer + 50)
    step = max(20, extent // 25)
    params = (WIDTH, HEIGHT, extent, step, WELL_A, WELL_R0)
    if params != _well_cache:
        _well_cache = params
    mesh_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    line_color = (20, 20, 20, 80) if sketch_mode else (80, 80, 120, 120)
    
    for x in range(-extent, extent + 1, step):
        prev = None
        for y in range(-extent, extent + 1, step):
            r = math.hypot(x, y)
            z = WELL_A / (1 + (r / WELL_R0) ** 2)
            z = min(z, WELL_MAX_DEPTH)
            pt = camera.world_to_screen((x, y), z)
            if prev:
                pygame.draw.aaline(mesh_surface, line_color, prev, pt)
            prev = pt
    for y in range(-extent, extent + 1, step):
        prev = None
        for x in range(-extent, extent + 1, step):
            r = math.hypot(x, y)
            z = WELL_A / (1 + (r / WELL_R0) ** 2)
            z = min(z, WELL_MAX_DEPTH)
            pt = camera.world_to_screen((x, y), z)
            if prev:
                pygame.draw.aaline(mesh_surface, line_color, prev, pt)
            prev = pt
    surface.blit(mesh_surface, (0, 0))

def recalculate_orbits(planets, scale=ORBIT_SCALE_DEFAULT):
    cumulative = []
    total = 0.0
    for d in SEGMENT_DISTANCES:
        total += d
        cumulative.append(total)

    current_neptune = planets[-1].orbit_radius
    k = (
        current_neptune
        - SUN_RADIUS
        - (len(SEGMENT_DISTANCES) - 1) * ORBIT_PADDING
    ) / cumulative[-1]

    radii = []
    r = SUN_RADIUS
    for i, dist in enumerate(SEGMENT_DISTANCES):
        r += dist * k
        r_scaled = r * scale
        planets[i].orbit_radius = r_scaled
        planets[i].body.position = (r_scaled, 0)
        radii.append(r_scaled)
        if i < len(SEGMENT_DISTANCES) - 1:
            r += ORBIT_PADDING

    DISTANCE_DATA.clear()
    inner = SUN_RADIUS * scale
    labels = SEGMENT_LABELS[CURRENT_LANG]
    for radius, label in zip(radii, labels):
        DISTANCE_DATA.append((inner, radius, label))
        inner = radius
    global OUTER_ORBIT_RADIUS
    OUTER_ORBIT_RADIUS = radii[-1]

def apply_approx_orbits(planets, scale=ORBIT_SCALE_DEFAULT):
    radii = []
    for idx, p in enumerate(planets):
        base = APPROX_ORBIT_RADII.get(p.name)
        if base is None:
            step = 55 + idx * 3
            base = BASE_INNER_RADIUS + idx * step
        r = base * scale
        p.orbit_radius = r
        p.body.position = (r, 0)
        radii.append(r)

    DISTANCE_DATA.clear()
    inner = SUN_RADIUS * scale
    labels = SEGMENT_LABELS[CURRENT_LANG]
    for radius, label in zip(radii, labels):
        DISTANCE_DATA.append((inner, radius, label))
        inner = radius
    global OUTER_ORBIT_RADIUS
    OUTER_ORBIT_RADIUS = radii[-1]

def draw_distance_reference(surface, camera, font, sketch_mode=False):
    start = camera.world_to_screen((SUN_DRAW_RADIUS, 0))
    end = camera.world_to_screen((DISTANCE_DATA[-1][1], 0))
    
    line_color = (50, 50, 50) if sketch_mode else (200, 200, 200)
    text_color = (0, 0, 0) if sketch_mode else (255, 255, 255)
    
    pygame.draw.aaline(surface, line_color, start, end)

    t = max(0.0, min(1.0, (camera.zoom - 0.5) / 0.5))
    alpha = int(t * 255)

    for inner_r, outer_r, label in DISTANCE_DATA:
        mid_x = (inner_r + outer_r) / 2.0
        mx, my = camera.world_to_screen((mid_x, 0))
        text_surf = font.render(label, True, text_color)
        text_surf.set_alpha(alpha)
        rect = text_surf.get_rect(midbottom=(mx, my - 5))
        surface.blit(text_surf, rect)

def draw_speed_panel(surface, font, selected_index):
    rects = []
    for i, speed in enumerate(SPEED_OPTIONS):
        rect = pygame.Rect(10 + i * 55, 10, 50, 25)
        rects.append(rect)
        color = (0, 200, 0) if i == selected_index else (200, 200, 200)
        pygame.draw.rect(surface, color, rect, 0 if i == selected_index else 2)
        text = font.render(f"{speed}x", True, (0, 0, 0))
        text_rect = text.get_rect(center=rect.center)
        surface.blit(text, text_rect)
    return rects

def draw_angle_buttons(surface, font, rects, focus, selected):
    for i, (label, rect, mode) in enumerate(
        zip(ANGLE_LABELS, rects, ANGLE_MODES)
    ):
        active = mode is selected
        color = (0, 200, 0) if active else (200, 200, 200)
        pygame.draw.rect(surface, color, rect, 0 if active else 2, border_radius=5)
        if i == focus:
            pygame.draw.rect(surface, (255, 255, 0), rect, 2, border_radius=5)
        text = font.render(label, True, (0, 0, 0))
        surface.blit(text, text.get_rect(center=rect.center))
    return rects

def draw_play_pause_buttons(surface, font, paused, play_rect, pause_rect):
    play_color = (0, 200, 0) if not paused else (150, 150, 150)
    pause_color = (200, 0, 0) if paused else (150, 150, 150)
    pygame.draw.rect(surface, play_color, play_rect)
    pygame.draw.rect(surface, pause_color, pause_rect)
    pygame.draw.rect(surface, (0, 0, 0), play_rect, 2)
    pygame.draw.rect(surface, (0, 0, 0), pause_rect, 2)
    play_txt = font.render(t("play"), True, (0, 0, 0))
    pause_txt = font.render(t("pause"), True, (0, 0, 0))
    surface.blit(play_txt, play_txt.get_rect(center=play_rect.center))
    surface.blit(pause_txt, pause_txt.get_rect(center=pause_rect.center))

def draw_sketch_button(surface, font, rect, sketch_mode):
    color = (0, 0, 0) if sketch_mode else (200, 200, 200)
    text_color = (255, 255, 255) if sketch_mode else (0, 0, 0)
    
    pygame.draw.rect(surface, color, rect, border_radius=5)
    pygame.draw.rect(surface, (0, 0, 0), rect, 2, border_radius=5)
    
    text = font.render(t("sketch_btn"), True, text_color)
    surface.blit(text, text.get_rect(center=rect.center))

def draw_keyboard_button(surface, font, rect, color):
    pygame.draw.rect(surface, color, rect, border_radius=5)
    pygame.draw.rect(surface, (0, 0, 0), rect, 2, border_radius=5)
    text = font.render(t("keyboard_functions"), True, (0, 0, 0))
    surface.blit(text, text.get_rect(center=rect.center))

def draw_keyboard_overlay(surface, font, pos):
    lines = [
        t("key_w"), t("key_s"), t("key_a"), t("key_d"), t("key_lr"),
        t("key_ud"), t("key_wheel"), t("key_r"), t("key_backspace"),
        t("key_space"), t("key_f11"),
    ]
    texts = [font.render(line, True, (0, 0, 0)) for line in lines]
    width = max(t.get_width() for t in texts) + 20
    height = len(texts) * 20 + 10
    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(
        overlay,
        (173, 216, 230, 180),
        overlay.get_rect(),
        border_radius=8,
    )
    for i, text in enumerate(texts):
        overlay.blit(text, (10, 5 + i * 20))
    surface.blit(overlay, pos)
    return pygame.Rect(pos, (width, height))

class Tooltip:
    def __init__(self, font):
        self.font = font
    def draw(self, surface, text, pos, orient="above"):
        txt = self.font.render(text, True, (255, 255, 255))
        if orient == "right":
            rect = txt.get_rect(midleft=(pos[0] + 6, pos[1]))
        else:
            rect = txt.get_rect(midbottom=(pos[0], pos[1] - 5))
        if rect.right > WIDTH - 6:
            rect.right = WIDTH - 6
        if rect.top < 6:
            rect.top = 6
        if rect.bottom > HEIGHT - 6:
            rect.bottom = HEIGHT - 6
        bg = pygame.Surface((rect.width + 6, rect.height + 4), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 180))
        surface.blit(bg, (rect.x - 3, rect.y - 2))
        surface.blit(txt, rect)

def create_book_icon(size: int) -> pygame.Surface:
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.rect(surf, (0, 0, 0, 100), (2, 2, size - 2, size - 2), border_radius=4)
    page = pygame.Surface((size - 4, size - 4), pygame.SRCALPHA)
    page.fill((245, 245, 245))
    pygame.draw.rect(page, (0, 0, 0), page.get_rect(), 1, border_radius=4)
    mid = page.get_width() // 2
    pygame.draw.line(page, (0, 0, 0), (mid, 3), (mid, page.get_height() - 3))
    surf.blit(page, (0, 0))
    return surf

def load_book_icon(size: int) -> pygame.Surface:
    path = os.path.join(os.path.dirname(__file__), "logobuku.png")
    try:
        img = pygame.image.load(path).convert_alpha()
        tile = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.rect(tile, (255, 255, 255), tile.get_rect(), border_radius=6)
        max_dim = size - 6
        w, h = img.get_size()
        scale = min(max_dim / w, max_dim / h)
        icon = pygame.transform.smoothscale(img, (int(w * scale), int(h * scale)))
        tile.blit(icon, icon.get_rect(center=tile.get_rect().center))
        return tile
    except Exception as exc:
        log(f"book icon load failed: {exc}; using fallback")
        return create_book_icon(size)

class BlurLayer:
    def __init__(self):
        self.surface = None

    def from_surface(self, src):
        w, h = src.get_size()
        small = pygame.transform.smoothscale(src, (max(1, w // 4), max(1, h // 4)))
        big = pygame.transform.smoothscale(small, (w, h))
        tint = pygame.Surface((w, h), pygame.SRCALPHA)
        tint.fill((0, 0, 0, 160))
        big.blit(tint, (0, 0))
        self.surface = big

    def draw(self, surface):
        if self.surface:
            surface.blit(self.surface, (0, 0))

class PlanetInfoPanel:
    def __init__(self, font):
        self.font = font

    def build(self, planet_name):
        info = get_planet_info(planet_name)
        dist_lbl = t("distance_lbl_sun") if planet_name == "Sun" else t("distance_lbl")
        rows = [
            (t("diameter_lbl"), info["diameter"]),
            (dist_lbl, info["distance"]),
            (t("period_lbl"), info["period"]),
        ]
        if "speed" in info:
            rows.append((t("speed_lbl"), info["speed"]))
        rows.append((t("life_lbl"), info["life"]))
        widths = [self.font.size(label)[0] for label, _ in rows]
        label_w = max(widths)
        value_w = max(self.font.size(val)[0] for _, val in rows)
        height = len(rows) * (self.font.get_linesize() + 4) + 10
        width = label_w + value_w + 30
        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.rect(surf, (240, 240, 240, 230), surf.get_rect(), border_radius=6)
        y = 5
        for label, val in rows:
            lbl = self.font.render(label, True, (0, 0, 0))
            val_s = self.font.render(val, True, (0, 0, 0))
            surf.blit(lbl, (10, y))
            surf.blit(val_s, (20 + label_w, y))
            y += self.font.get_linesize() + 4
        return surf

class PlanetOverlay:
    def __init__(self, font):
        self.font = font
        self.title_font = pygame.font.SysFont("arial", 32)
        self.italic = pygame.font.SysFont("georgia", 18, italic=True)
        self.italic_bold = pygame.font.SysFont("georgia", 18, bold=True, italic=True)
        self.info_panel = PlanetInfoPanel(pygame.font.SysFont("consolas", 16))
        self.planet = None
        self.overlay = None
        self.close_rect = None
        self.right_rect = None
        self.summary_rect = None
        self.detail_point_rects = [] # (rect_rel_to_overlay, text_string, point_index)
        self.hover_point_index = None

    def open(self, planet):
        self.planet = planet
        log(f"overlay open {planet.name} info={get_planet_info(planet.name)}")
        self._rebuild()

    def _rebuild(self):
        self.detail_point_rects = []
        info = get_planet_info(self.planet.name)
        left_w = 260
        left_h = 260
        left = pygame.Surface((left_w, left_h), pygame.SRCALPHA)
        pygame.draw.rect(left, (240, 240, 240, 230), left.get_rect(), border_radius=6)
        title = self.title_font.render(self.planet.name, True, (0, 0, 0))
        left.blit(title, title.get_rect(midtop=(left_w / 2, 10)))
        cx, cy = left_w / 2, left_h / 2 + 10
        radius = 60
        pygame.draw.circle(left, self.planet.color, (int(cx), int(cy)), radius)
        pygame.draw.circle(left, (255, 255, 255), (int(cx), int(cy)), radius + 4, 2)

        right = self.info_panel.build(self.planet.name)

        summary_text = info["summary_italic"]
        gap = 20
        summary_w = max(right.get_width(), min(max(50, WIDTH - (left_w + gap + 40)), 500))
        wrap_w = summary_w - 20
        lines = []
        
        raw_paragraphs = summary_text.split('\n')
        for para in raw_paragraphs:
            words = para.split(' ')
            line_buf = ""
            for idx, word in enumerate(words):
                test = (line_buf + " " + word).strip() if line_buf else word
                if self.italic.size(test)[0] <= wrap_w:
                    line_buf = test
                else:
                    lines.append(line_buf)
                    line_buf = word
            if line_buf:
                lines.append(line_buf)
                    
        summary_h = len(lines) * self.italic.get_linesize()
        summary_box = pygame.Surface((summary_w, summary_h + 20), pygame.SRCALPHA)
        pygame.draw.rect(summary_box, (240, 240, 240, 230), summary_box.get_rect(), border_radius=6)
        
        lh = self.italic.get_linesize()
        
        top_h = max(left_h, right.get_height())
        w = left_w + gap + max(right.get_width(), summary_w) + 20
        h = top_h + summary_box.get_height() + 80
        
        summary_offset_x = left_w + gap
        summary_offset_y = 40 + right.get_height() + 10
        
        for i, line in enumerate(lines):
            txt = self.italic.render(line, True, (0, 0, 0))
            y_pos = 10 + i * lh
            summary_box.blit(txt, (10, y_pos))
            
            # Logic untuk mendeteksi poin 1-6 di Mars & Earth
            if self.planet.name in ["Mars", "Earth"]:
                stripped = line.strip()
                point_idx = None
                if stripped.startswith("1."): point_idx = 1
                elif stripped.startswith("2."): point_idx = 2
                elif stripped.startswith("3."): point_idx = 3
                elif stripped.startswith("4."): point_idx = 4
                elif stripped.startswith("5."): point_idx = 5
                elif stripped.startswith("6."): point_idx = 6
                
                # Jika baris ini adalah awal poin atau kelanjutan (sederhana: anggap hanya baris yg ada angka depannya bisa diklik agar rapi, atau bisa semua baris)
                # Agar UX bagus, kita deteksi baris yang ada angkanya saja sebagai trigger 'button'
                if point_idx is not None:
                    r = pygame.Rect(10, y_pos, txt.get_width(), lh)
                    r.move_ip(summary_offset_x, summary_offset_y)
                    self.detail_point_rects.append((r, line, point_idx))

        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (30, 30, 30, 180), overlay.get_rect(), border_radius=10)
        overlay.blit(left, (10, 40))
        self.right_rect = overlay.blit(right, (left_w + gap, 40))
        self.summary_rect = overlay.blit(summary_box, (summary_offset_x, summary_offset_y))
        
        hint = self.font.render(t("hint_close"), True, (255, 255, 255))
        overlay.blit(hint, hint.get_rect(midbottom=(w / 2, h - 10)))
        close_size = 36
        self.close_rect = pygame.Rect(w - close_size - 5, 5, close_size, close_size)
        pygame.draw.rect(overlay, (200, 80, 80), self.close_rect)
        pygame.draw.rect(overlay, (0, 0, 0), self.close_rect, 2)
        x_text = self.title_font.render("×", True, (0, 0, 0))
        overlay.blit(x_text, x_text.get_rect(center=self.close_rect.center))
        self.overlay = overlay

    def draw(self, surface):
        self.overlay_rect = self.overlay.get_rect(center=(WIDTH / 2, HEIGHT / 2))
        
        self.hover_point_index = None
        # Gunakan pengecekan generic agar Earth juga bisa
        if self.planet.name in ["Mars", "Earth"] and self.detail_point_rects:
            mouse_pos = pygame.mouse.get_pos()
            rel_mx = mouse_pos[0] - self.overlay_rect.x
            rel_my = mouse_pos[1] - self.overlay_rect.y
            
            for r, text, idx in self.detail_point_rects:
                # Perbesar area hit sedikit agar mudah diklik
                hit_r = r.inflate(0, 4)
                if hit_r.collidepoint(rel_mx, rel_my):
                    self.hover_point_index = idx
                    # Highlight Text Line yg sedang dihover
                    abs_r = r.move(self.overlay_rect.topleft)
                    lift_y = -4
                    padding_x = 4
                    highlight_rect = pygame.Rect(
                        abs_r.x - padding_x, 
                        abs_r.y + lift_y, 
                        abs_r.width + padding_x * 2, 
                        abs_r.height
                    )
                    pygame.draw.rect(surface, (255, 255, 255), highlight_rect, border_radius=4)
                    txt_surf = self.italic_bold.render(text, True, (0, 0, 0))
                    surface.blit(txt_surf, (abs_r.x, abs_r.y + lift_y))
                    break # Hanya satu yang bisa dihover
        
        surface.blit(self.overlay, self.overlay_rect.topleft)
        
        # Redraw highlight on top of overlay if needed (sudah dilakukan di atas sebelum blit overlay agar di bawah text? Tidak, overlay ada transparansinya, urutan: 
        # 1. Background (sudah)
        # 2. Highlight Box (Putih)
        # 3. Text Bold Hitam (Agar jelas terbaca di atas putih)
        # 4. Overlay Panel (Transparan) -> ini akan menimpa highlight. 
        # Jadi urutan yang benar: Draw Overlay dulu, lalu Draw Highlight di ATAS overlay.
        
        # Koreksi urutan draw agar highlight muncul di atas panel summary box yg semi transparan
        if self.hover_point_index is not None:
             for r, text, idx in self.detail_point_rects:
                 if idx == self.hover_point_index:
                    abs_r = r.move(self.overlay_rect.topleft)
                    lift_y = -4
                    padding_x = 4
                    highlight_rect = pygame.Rect(
                        abs_r.x - padding_x, 
                        abs_r.y + lift_y, 
                        abs_r.width + padding_x * 2, 
                        abs_r.height
                    )
                    pygame.draw.rect(surface, (255, 255, 255), highlight_rect, border_radius=4)
                    txt_surf = self.italic_bold.render(text, True, (0, 0, 0))
                    surface.blit(txt_surf, (abs_r.x, abs_r.y + lift_y))

        self.close_abs = self.close_rect.move(self.overlay_rect.topleft)

    def handle_event(self, event, planets):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "close"
            elif event.key in (pygame.K_RIGHT, pygame.K_PAGEDOWN):
                self._switch_planet(planets, 1)
            elif event.key in (pygame.K_LEFT, pygame.K_PAGEUP):
                self._switch_planet(planets, -1)
        elif event.type == pygame.MOUSEWHEEL:
            self._scroll_planet(planets, event.y)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.close_abs.collidepoint(event.pos):
                return "close"
            if self.hover_point_index is not None:
                # Return format baru: open_mars_detail_{index}
                return f"open_mars_detail_{self.hover_point_index}"
            if not self.overlay_rect.collidepoint(event.pos):
                return "close"
        return None

    def _switch_planet(self, planets, delta):
        idx = planets.index(self.planet)
        idx = (idx + delta) % len(planets)
        self.planet = planets[idx]
        log(f"overlay switch {self.planet.name}")
        self._rebuild()

    def _scroll_planet(self, planets, wheel_y):
        sequence = planets
        idx = sequence.index(self.planet)
        if wheel_y > 0 and idx > 0:
            self.planet = sequence[idx - 1]
        elif wheel_y < 0 and idx < len(sequence) - 1:
            self.planet = sequence[idx + 1]
        else:
            return
        log(f"overlay scroll {self.planet.name}")
        self._rebuild()

class LanguageModal:
    def __init__(self, font):
        self.font = font
        self.blur = BlurLayer()
        self.panel = None
        self.panel_rect = None
        self.buttons = []

    def open(self, background):
        self.blur.from_surface(background)
        w, h = 300, 160
        self.panel = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(self.panel, (240, 240, 240, 230), self.panel.get_rect(), border_radius=8)
        flag_id = pygame.Surface((32, 20))
        flag_id.fill((255, 255, 255))
        pygame.draw.rect(flag_id, (217, 0, 0), (0, 0, 32, 10))
        flag_en = pygame.Surface((32, 20))
        flag_en.fill((255, 255, 255))
        pygame.draw.rect(flag_en, (200, 0, 0), (0, 8, 32, 4))
        pygame.draw.rect(flag_en, (200, 0, 0), (14, 0, 4, 20))
        btn_w, btn_h = 120, 40
        id_rect = pygame.Rect(30, h / 2 - btn_h / 2, btn_w, btn_h)
        en_rect = pygame.Rect(w - btn_w - 30, h / 2 - btn_h / 2, btn_w, btn_h)
        self.buttons = [(id_rect, "id"), (en_rect, "en")]
        for rect, code in self.buttons:
            pygame.draw.rect(self.panel, (200, 200, 200), rect, border_radius=6)
            flag = flag_id if code == "id" else flag_en
            self.panel.blit(flag, flag.get_rect(midleft=(rect.left + 10, rect.centery)))
            label = "Indonesia" if code == "id" else "English"
            txt = self.font.render(label, True, (0, 0, 0))
            self.panel.blit(txt, txt.get_rect(midleft=(rect.left + 50, rect.centery)))
        self.panel_rect = self.panel.get_rect(center=(WIDTH / 2, HEIGHT / 2))

    def draw(self, surface):
        self.blur.draw(surface)
        surface.blit(self.panel, self.panel_rect.topleft)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "close"
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            rel = (event.pos[0] - self.panel_rect.left, event.pos[1] - self.panel_rect.top)
            for rect, code in self.buttons:
                if rect.collidepoint(rel):
                    return code
        return None

class TimeInfoModal:
    def __init__(self, font):
        self.font = font
        self.title_font = pygame.font.SysFont("arial", 26, bold=True)
        self.body_font = pygame.font.SysFont("couriernew", 15)
        self.blur = BlurLayer()
        self.panel = None
        self.panel_rect = None
        self.close_rect = None
        self.pad = 20

    def open(self, background):
        self.blur.from_surface(background)
        self._build()

    def _build(self):
        lines = textwrap.wrap(t("time_info_body"), width=70)
        body_surfs = [self.body_font.render(line, True, (0, 0, 0)) for line in lines]
        body_h = len(body_surfs) * self.body_font.get_linesize()
        title_surf = self.title_font.render(t("time_info_title"), True, (0, 0, 0))
        panel_w = max(max((s.get_width() for s in body_surfs), default=0), title_surf.get_width()) + self.pad * 2
        panel_w = min(max(panel_w, 560), 680)
        panel_h = self.pad + title_surf.get_height() + 10 + body_h + self.pad
        self.panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        self.panel.fill((240, 240, 240, 230))
        pygame.draw.rect(self.panel, (0, 0, 0), self.panel.get_rect(), 2, border_radius=8)
        self.panel.blit(title_surf, title_surf.get_rect(midtop=(panel_w / 2, self.pad)))
        y = self.pad + title_surf.get_height() + 10
        for surf in body_surfs:
            self.panel.blit(surf, surf.get_rect(center=(panel_w / 2, y + surf.get_height() / 2)))
            y += self.body_font.get_linesize()
        self.close_rect = pygame.Rect(panel_w - 30 - self.pad / 2, self.pad / 2, 30, 30)
        pygame.draw.rect(self.panel, (200, 200, 200), self.close_rect, border_radius=4)
        pygame.draw.rect(self.panel, (0, 0, 0), self.close_rect, 1, border_radius=4)
        cross = self.font.render("×", True, (0, 0, 0))
        self.panel.blit(cross, cross.get_rect(center=self.close_rect.center))
        self.panel_rect = self.panel.get_rect(center=(WIDTH / 2, HEIGHT / 2))

    def draw(self, surface):
        self.blur.draw(surface)
        surface.blit(self.panel, self.panel_rect.topleft)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "close"
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not self.panel_rect.collidepoint(event.pos):
                return "close"
            rel = (event.pos[0] - self.panel_rect.left, event.pos[1] - self.panel_rect.top)
            if self.close_rect.collidepoint(rel):
                return "close"
        return None

class DataSourcesModal:
    def __init__(self, font, _small_font):
        self.font = font
        self.mono_font = pygame.font.SysFont("couriernew", 15)
        self.bold_font = pygame.font.SysFont("couriernew", 15, bold=True)
        self.italic_font = pygame.font.SysFont("couriernew", 15, italic=True)
        self.title_font = pygame.font.SysFont("arial", 26, bold=True)
        self.blur = BlurLayer()
        self.panel_rect = None
        self.view_rect = None
        self.content_surf = None
        self.link_rects = []
        self.scroll = 0
        self.max_scroll = 0
        self.close_rect = None
        self.focus = -1
        self.pad = 12
        self.margin = 38

    def open(self, background):
        self.blur.from_surface(background)
        self._build()

    def _build(self):
        self.margin = max(24, min(64, int(0.03 * min(WIDTH, HEIGHT))))
        panel_w = WIDTH - 2 * self.margin
        panel_h = HEIGHT - 2 * self.margin
        self.panel_rect = pygame.Rect(self.margin, self.margin, panel_w, panel_h)
        title_h = self.title_font.get_height()
        self.view_rect = pygame.Rect(
            self.pad,
            title_h + self.pad * 2,
            panel_w - self.pad * 2,
            panel_h - (title_h + self.pad * 3),
        )

        text_w = self.view_rect.width
        line_h = self.mono_font.get_linesize()
        lines, link_rects, content_h = self._layout_content(text_w, line_h)
        self.content_surf = pygame.Surface((text_w, content_h), pygame.SRCALPHA)
        for surf, (x, y) in lines:
            self.content_surf.blit(surf, (x, y))
        self.link_rects = link_rects
        self.max_scroll = max(0, content_h - self.view_rect.height)
        self.scroll = min(self.scroll, self.max_scroll)

        self.close_rect = pygame.Rect(panel_w - 30 - self.pad, self.pad, 30, 30)
        self.title_surf = self.title_font.render(t("sources_title"), True, (0, 0, 0))

    def _layout_content(self, width, line_h):
        text = EXACT_SOURCES_ID if CURRENT_LANG == "id" else EXACT_SOURCES_EN
        items = [ln for ln in text.split("\n") if ln]
        y = 0
        rendered = []
        link_rects = []
        space_w = self.mono_font.size(" ")[0]
        for item in items:
            tokens = self._parse_item(item)
            line_tokens = []
            line_width = 0
            lines_for_item = []
            for tok in tokens:
                font = (
                    self.bold_font
                    if tok.style == "bold"
                    else self.italic_font
                    if tok.style == "italic"
                    else self.mono_font
                )
                w = font.size(tok.text)[0]
                add = w if not line_tokens else line_width + space_w + w
                if line_tokens and add > width:
                    lines_for_item.append(line_tokens)
                    line_tokens = [tok]
                    line_width = w
                else:
                    if line_tokens:
                        line_width += space_w
                    line_tokens.append(tok)
                    line_width = add
            if line_tokens:
                lines_for_item.append(line_tokens)
            for lt in lines_for_item:
                surf, rects = self._render_line(lt, width)
                rendered.append((surf, (0, y)))
                for r, url in rects:
                    link_rects.append((r.move(0, y), url))
                y += line_h
            y += line_h
        return rendered, link_rects, y

    def _parse_item(self, line):
        Token = SimpleNamespace
        m = re.match(r"^(\d+\.)\s*\*?\s*(.*)$", line)
        if not m:
            return [Token(text=line, url=None, style="regular")]
        number, rest = m.groups()
        m2 = re.match(r"'([^']+)'\s*->\s*'([^']+)'", rest)
        if not m2:
            return [Token(text=line, url=None, style="regular")]
        what, src_links = m2.groups()
        if ":" in src_links:
            source, links_part = src_links.split(":", 1)
        else:
            source, links_part = src_links, ""
        links = [s.strip() for s in links_part.split("|") if s.strip()]
        seen = set()
        tokens = [Token(text=number, url=None, style="regular")]
        for word in what.split():
            tokens.append(Token(text=word, url=None, style="bold"))
        tokens.append(Token(text="->", url=None, style="regular"))
        for word in source.strip().split():
            tokens.append(Token(text=word, url=None, style="regular"))
        if links:
            tokens.append(Token(text=":", url=None, style="regular"))
            for i, link in enumerate(links):
                match = re.match(r"\[([^\]]+)\]\((https?://[^)]+)\)", link)
                if match:
                    label, url = match.groups()
                else:
                    label, url = link, link
                norm = self._normalise(url)
                if norm in seen:
                    continue
                seen.add(norm)
                tokens.append(Token(text=label, url=url, style="italic"))
                if i < len(links) - 1:
                    tokens.append(Token(text="|", url=None, style="regular"))
        return tokens

    def _render_line(self, tokens, width):
        line_surf = pygame.Surface((width, self.mono_font.get_linesize()), pygame.SRCALPHA)
        space_w = self.mono_font.size(" ")[0]
        x = 0
        link_rects = []
        for i, tok in enumerate(tokens):
            font = (
                self.bold_font
                if tok.style == "bold"
                else self.italic_font
                if tok.style == "italic"
                else self.mono_font
            )
            surf = font.render(tok.text, True, (0, 0, 0))
            line_surf.blit(surf, (x, 0))
            if tok.url:
                link_rects.append((pygame.Rect(x, 0, surf.get_width(), surf.get_height()), tok.url))
            x += surf.get_width()
            if i < len(tokens) - 1:
                x += space_w
        return line_surf, link_rects

    def _normalise(self, url: str) -> str:
        parsed = urlsplit(url.strip())
        q = [(k, v) for k, v in parse_qsl(parsed.query) if not k.lower().startswith("utm_")]
        query = urlencode(q)
        path = parsed.path.rstrip("/")
        return urlunsplit((parsed.scheme, parsed.netloc, path, query, ""))

    def draw(self, surface):
        self.blur.draw(surface)
        panel = pygame.Surface(self.panel_rect.size, pygame.SRCALPHA)
        panel.fill((240, 240, 240, 230))
        pygame.draw.rect(panel, (0, 0, 0), panel.get_rect(), 2, border_radius=8)
        panel.blit(self.title_surf, self.title_surf.get_rect(midtop=(self.panel_rect.width / 2, self.pad)))
        pygame.draw.rect(panel, (200, 200, 200), self.close_rect, border_radius=4)
        pygame.draw.rect(panel, (0, 0, 0), self.close_rect, 1, border_radius=4)
        cross = self.font.render("×", True, (0, 0, 0))
        panel.blit(cross, cross.get_rect(center=self.close_rect.center))
        panel.set_clip(self.view_rect)
        panel.blit(self.content_surf, (self.pad, self.view_rect.y - self.scroll))
        panel.set_clip(None)
        surface.blit(panel, self.panel_rect.topleft)

        mouse = pygame.mouse.get_pos()
        for idx, (rect, url) in enumerate(self.link_rects):
            screen_rect = rect.move(
                self.panel_rect.left + self.pad,
                self.panel_rect.top + self.view_rect.y - self.scroll,
            )
            underline = screen_rect.collidepoint(mouse) or self.focus == idx
            if underline:
                pygame.draw.line(
                    surface,
                    (0, 0, 200),
                    (screen_rect.left, screen_rect.bottom),
                    (screen_rect.right, screen_rect.bottom),
                    1,
                )

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "close"
            if event.key == pygame.K_TAB and self.link_rects:
                self.focus = (self.focus + 1) % len(self.link_rects)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE) and self.focus != -1:
                open_url(self.link_rects[self.focus][1])
            elif event.key == pygame.K_DOWN:
                self.scroll = min(self.scroll + 20, self.max_scroll)
            elif event.key == pygame.K_UP:
                self.scroll = max(self.scroll - 20, 0)
            elif event.key == pygame.K_PAGEDOWN:
                self.scroll = min(self.scroll + self.view_rect.height, self.max_scroll)
            elif event.key == pygame.K_PAGEUP:
                self.scroll = max(self.scroll - self.view_rect.height, 0)
            return None
        if event.type == pygame.MOUSEWHEEL:
            if self.panel_rect.collidepoint(pygame.mouse.get_pos()):
                self.scroll = min(max(self.scroll - event.y * 20, 0), self.max_scroll)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not self.panel_rect.collidepoint(event.pos):
                return "close"
            rel = (event.pos[0] - self.panel_rect.left, event.pos[1] - self.panel_rect.top)
            if self.close_rect.collidepoint(rel):
                return "close"
            if self.view_rect.collidepoint(rel):
                content_rel = (
                    rel[0] - self.view_rect.x,
                    rel[1] - self.view_rect.y + self.scroll,
                )
                for idx, (rect, url) in enumerate(self.link_rects):
                    if rect.collidepoint(content_rel):
                        open_url(url)
                        self.focus = idx
                        break
        return None

def draw_debug_overlay(surface, camera, font, input_vec):
    origin = camera.world_to_screen(camera.pos)
    x_axis = camera.world_to_screen(camera.pos + Vector2(50, 0))
    y_axis = camera.world_to_screen(camera.pos + Vector2(0, 50))
    pygame.draw.line(surface, (255, 0, 0), origin, x_axis, 1)
    pygame.draw.line(surface, (0, 255, 0), origin, y_axis, 1)

    grid_extent = 200
    step = 50
    for gx in range(-grid_extent, grid_extent + 1, step):
        start = camera.world_to_screen((camera.pos.x + gx, camera.pos.y - grid_extent))
        end = camera.world_to_screen((camera.pos.x + gx, camera.pos.y + grid_extent))
        pygame.draw.aaline(surface, (60, 60, 60), start, end)
    for gy in range(-grid_extent, grid_extent + 1, step):
        start = camera.world_to_screen((camera.pos.x - grid_extent, camera.pos.y + gy))
        end = camera.world_to_screen((camera.pos.x + grid_extent, camera.pos.y + gy))
        pygame.draw.aaline(surface, (60, 60, 60), start, end)

    info = f"pos=({camera.pos.x:.1f},{camera.pos.y:.1f}) rot={math.degrees(camera.rot):.1f}° zoom={camera.zoom:.2f} m={input_vec.x:.2f},{input_vec.y:.2f}"
    text = font.render(info, True, (255, 255, 0))
    surface.blit(text, (10, HEIGHT - 20))

def camera_self_test():
    pygame.init()
    cam = Camera2D()
    expected = Vector2()
    seq = [Vector2(0, 1), Vector2(1, 0), Vector2(0, -1), Vector2(-1, 0)]
    dt = 1 / 60.0
    for i in range(120):
        cam.rot = random.uniform(0, 2 * math.pi)
        cam._update_cache()
        move = seq[i % len(seq)]
        cam.pos += move * PAN_SPEED_WORLD * dt
        expected += move * PAN_SPEED_WORLD * dt
    if (cam.pos - expected).length() < 1e-5:
        print("Camera self-test PASS")
    else:
        print("Camera self-test FAIL", cam.pos, expected)
    pygame.quit()

# ==============================================================================
# FUNGSI LISENSI
# ==============================================================================

def check_license_locally():
    """Cek apakah file lisensi ada. Tidak memverifikasi ke server (mode offline)."""
    if os.path.exists(LICENSE_FILE):
        return True
    return False

def activate_license_online(key, hwid):
    """Mengontak server Flask untuk aktivasi."""
    url = f"{LICENSE_SERVER_URL}/activate"
    payload = {"key": key, "hwid": hwid}
    try:
        r = requests.post(url, json=payload, timeout=10)
        data = r.json()
        if r.status_code == 200 and data.get("status") == "success":
            return True, data.get("message")
        else:
            return False, data.get("message", "Unknown Server Error")
    except Exception as e:
        return False, f"Connection Error: {str(e)}"

def draw_blueprint_grid(surface):
    """Menggambar grid blueprint halus di background."""
    w, h = surface.get_size()
    # Warna background utama blueprint (biru gelap)
    # Sesuaikan dengan warna saat aplikasi simulasi di mulai: (10, 10, 30)
    bg_color = (10, 10, 30)
    surface.fill(bg_color)
    
    # Warna garis grid (biru/abu-abu halus transparan)
    line_color_solid = (40, 40, 70) 
    
    step = 40
    for x in range(0, w, step):
        pygame.draw.line(surface, line_color_solid, (x, 0), (x, h))
    for y in range(0, h, step):
        pygame.draw.line(surface, line_color_solid, (0, y), (w, y))

def get_clipboard_text():
    """Mengambil teks dari clipboard sistem."""
    # Cara 1: Coba pygame.scrap (jika disupport dan diinit)
    if pygame.scrap.get_init():
        content = pygame.scrap.get(pygame.SCRAP_TEXT)
        if content:
            try:
                return content.decode("utf-8").strip()
            except:
                pass
    
    # Cara 2: Fallback ke Tkinter (biasanya ada di instalasi python standar)
    try:
        import tkinter
        tk = tkinter.Tk()
        tk.withdraw() # Sembunyikan window utama
        text = tk.clipboard_get()
        tk.destroy()
        return text
    except:
        return ""

def check_trial_history_used(hwid):
    """Cek apakah HWID ini sudah pernah menggunakan trial."""
    if os.path.exists("trial_history.dat"):
        try:
            with open("trial_history.dat", "r") as f:
                content = f.read()
                if hwid in content:
                    return True
        except:
            pass
    return False

def mark_trial_used(hwid):
    """Tandai HWID ini sudah menggunakan trial."""
    try:
        with open("trial_history.dat", "a") as f:
            f.write(f"{hwid}|USED\n")
    except:
        pass

def license_screen(screen, target_key=None, startup_message=None):
    """
    Loop khusus untuk input serial number sebelum masuk ke main game.
    target_key: Jika diisi, user WAJIB memasukkan key yang sama dengan ini.
    """
    clock = pygame.time.Clock()
    font_main_title = pygame.font.SysFont("arial", 48, bold=True)
    font_title = pygame.font.SysFont("arial", 30, bold=True)
    font_input = pygame.font.SysFont("couriernew", 30, bold=True)
    font_msg = pygame.font.SysFont("arial", 20)
    font_quote = pygame.font.SysFont("georgia", 18, italic=True)
    font_small = pygame.font.SysFont("arial", 14)
    # Font khusus tombol trial (italic, bold)
    font_trial_btn = pygame.font.SysFont("arial", 16, bold=True, italic=True) 
    
    input_box = pygame.Rect(WIDTH // 2 - 200, HEIGHT // 2 - 25, 400, 50)
    # Geser tombol ACTIVATE ke bawah agar tidak menimpa link trial
    btn_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 100, 200, 50)
    
    color_inactive = (100, 100, 100)
    color_active = (100, 200, 255) # Biru muda blueprint
    color = color_inactive
    active = False
    text = ''
    
    # Pesan default atau pesan startup (misal: trial expired)
    message = startup_message if startup_message else "ENTER SERIAL NUMBER"
    msg_color = (255, 50, 50) if startup_message else (255, 255, 255)
    
    state = LicenseState.INPUT_KEY
    hwid = get_hwid()
    
    # Mode License: LIFETIME vs TRIAL
    license_mode = "LIFETIME" # Default
    
    # Timer untuk backspace
    last_backspace_time = 0
    backspace_interval = 50 # ms
    backspace_delay = 400 # ms
    
    running = True
    while running:
        current_time = pygame.time.get_ticks()
        
        # Hitung posisi tombol trial (di bawah kiri input box)
        trial_btn_txt_str = "coba free trial for 3 day" if license_mode == "LIFETIME" else "pergi ke lifetime"
        trial_btn_surf = font_trial_btn.render(trial_btn_txt_str, True, (200, 200, 255))
        # Garis bawah manual
        pygame.draw.line(trial_btn_surf, (200, 200, 255), (0, trial_btn_surf.get_height()-2), (trial_btn_surf.get_width(), trial_btn_surf.get_height()-2), 1)
        
        trial_btn_rect = trial_btn_surf.get_rect(topleft=(input_box.left, input_box.bottom + 10))
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if input_box.collidepoint(event.pos):
                    # Input box only active in Lifetime mode
                    if license_mode == "LIFETIME":
                        active = not active
                    else:
                        active = False
                else:
                    active = False
                color = color_active if active else color_inactive
                
                # Cek Tombol Trial/Lifetime Toggle
                if trial_btn_rect.collidepoint(event.pos):
                    if license_mode == "LIFETIME":
                        license_mode = "TRIAL"
                        message = "PRESS ACTIVATE TO START TRIAL"
                        msg_color = (255, 255, 255)
                    else:
                        license_mode = "LIFETIME"
                        message = "ENTER SERIAL NUMBER"
                        msg_color = (255, 255, 255)
                    text = "" # Reset input saat ganti mode
                
                # Cek Tombol Activate
                if state == LicenseState.INPUT_KEY and btn_rect.collidepoint(event.pos):
                    if license_mode == "TRIAL":
                        # Trial: Langsung aktivasi tanpa cek panjang text
                        state = LicenseState.ACTIVATING
                    else:
                        # Lifetime: Cek panjang key
                        if len(text) > 5:
                            # Jika mode Lifetime, cek validasi lokal
                            if license_mode == "LIFETIME" and target_key and text.strip() != target_key.strip():
                                 import tkinter
                                 from tkinter import messagebox
                                 try:
                                     root = tkinter.Tk()
                                     root.withdraw()
                                     messagebox.showerror("Error", "Serial number anda bukan yang ini, masukkan yang telah diberikan oleh penjual")
                                     root.destroy()
                                 except:
                                     pass
                                 message = "SERIAL NUMBER SALAH (BEDA DENGAN SEBELUMNYA)"
                                 msg_color = (255, 50, 50)
                            else:
                                state = LicenseState.ACTIVATING
            
            if event.type == pygame.KEYDOWN:
                if active and license_mode == "LIFETIME":
                    if event.key == pygame.K_RETURN:
                        if len(text) > 5:
                            # Logic Enter sama dengan Klik Activate
                            if license_mode == "LIFETIME" and target_key and text.strip() != target_key.strip():
                                 import tkinter
                                 from tkinter import messagebox
                                 try:
                                     root = tkinter.Tk()
                                     root.withdraw()
                                     messagebox.showerror("Error", "Serial number anda bukan yang ini, masukkan yang telah diberikan oleh penjual")
                                     root.destroy()
                                 except:
                                     pass
                                 message = "SERIAL NUMBER SALAH"
                                 msg_color = (255, 50, 50)
                            else:
                                state = LicenseState.ACTIVATING
                                
                    elif event.key == pygame.K_BACKSPACE:
                        text = text[:-1]
                        last_backspace_time = current_time + backspace_delay
                    elif event.key == pygame.K_DELETE: # Fitur delete
                        text = "" 
                    elif event.key == pygame.K_a and (event.mod & pygame.KMOD_CTRL):
                        # Ctrl+A Select All (Simulasi visual dengan print atau flash?)
                        # Di Pygame input simple string, Ctrl+A biasanya untuk replace.
                        # Kita buat agar user bisa langsung delete semua setelah Ctrl+A -> Backspace/Del
                        # Tapi di sini kita simpelkan: Ctrl+A -> Print 'Selected' di console debug atau sekadar flag.
                        # Instruksi bilang: "aktifkan pula fungsi fitur mendelete seluruh teks serial number yang dimasukkan jika teks di ctrl-A"
                        # Ini ambigu: apakah Ctrl+A langsung delete? Atau Ctrl+A select lalu delete?
                        # Biasanya Ctrl+A select all. Lalu user tekan Backspace.
                        # Untuk mempermudah sesuai prompt: "aktifkan fungsi fitur mendelete seluruh teks... jika teks di ctrl-A"
                        # Saya akan buat Ctrl+A langsung menghapus teks atau "Select All" effect lalu next char replaces.
                        # Tapi paling aman: Ctrl+A = Select All logic is complex in simple UI.
                        # Saya akan implementasi Ctrl+A -> Kosongkan text (Clear). Simpel dan efektif.
                        text = "" 
                    elif event.key == pygame.K_v and (event.mod & pygame.KMOD_CTRL):
                        clip = get_clipboard_text()
                        if clip: text += clip.upper().strip()
                    elif event.key == pygame.K_c and (event.mod & pygame.KMOD_CTRL):
                        try:
                            import tkinter
                            tk = tkinter.Tk()
                            tk.withdraw()
                            tk.clipboard_clear()
                            tk.clipboard_append(text)
                            tk.update()
                            tk.destroy()
                        except: pass
                    elif event.key == pygame.K_x and (event.mod & pygame.KMOD_CTRL):
                        try:
                            import tkinter
                            tk = tkinter.Tk()
                            tk.withdraw()
                            tk.clipboard_clear()
                            tk.clipboard_append(text)
                            tk.update()
                            tk.destroy()
                            text = ""
                        except: pass
                    else:
                        if event.unicode.isprintable() and len(text) < 50:
                            text += event.unicode.upper()

        # Handle Backspace Hold
        keys = pygame.key.get_pressed()
        if keys[pygame.K_BACKSPACE] and active:
            if current_time > last_backspace_time:
                text = text[:-1]
                last_backspace_time = current_time + backspace_interval

        # Background Blueprint
        draw_blueprint_grid(screen)
        
        # Logic Aktivasi
        if state == LicenseState.ACTIVATING:
            # Jika Trial Mode, Cek History Dulu
            blocked_trial = False
            if license_mode == "TRIAL":
                # Cek apakah sudah pernah pakai trial
                if check_trial_history_used(hwid):
                    message = "masa free trial teruss ehe.. ayokk gasss lifetime.."
                    msg_color = (255, 50, 50)
                    state = LicenseState.INPUT_KEY
                    blocked_trial = True
                else:
                    # Automatic Activation for Trial (Local Check / Skip Server Key Check)
                    # We create a dummy success state locally for Trial
                    start_time = time.time()
                    # Generate a dummy key for file consistency
                    dummy_trial_key = f"AUTO-TRIAL-{hwid}"
                    
                    # Simpan data lisensi lokal
                    try:
                        with open(LICENSE_FILE, "w") as f:
                             # Format: TRIAL|HWID|KEY|START_TIMESTAMP
                            f.write(f"TRIAL|{hwid}|{dummy_trial_key}|{start_time}")
                        mark_trial_used(hwid)
                        
                        message = "TRIAL ACTIVATED!"
                        msg_color = (0, 255, 0)
                        state = LicenseState.SUCCESS
                        text = dummy_trial_key # Untuk return value
                    except Exception as e:
                        message = f"ERROR WRITING FILE: {e}"
                        msg_color = (255, 50, 50)
                        state = LicenseState.INPUT_KEY
            
            if not blocked_trial and license_mode == "LIFETIME":
                # Draw overlay loading
                msg_surf = font_msg.render("CONTACTING SERVER...", True, (255, 255, 0))
                screen.blit(msg_surf, msg_surf.get_rect(center=(WIDTH//2, HEIGHT//2 + 120)))
                pygame.display.flip()
                
                success, server_msg = activate_license_online(text, hwid)
                if success:
                    message = "ACTIVATION SUCCESSFUL!"
                    msg_color = (0, 255, 0)
                    state = LicenseState.SUCCESS
                    
                    # Simpan data lisensi
                    with open(LICENSE_FILE, "w") as f:
                        # Format: ACTIVATED|HWID|KEY
                        f.write(f"ACTIVATED|{hwid}|{text}")
                else:
                    message = f"FAILED: {server_msg}"
                    msg_color = (255, 50, 50)
                    state = LicenseState.INPUT_KEY
        
        elif state == LicenseState.SUCCESS:
            txt_surface = font_input.render(text, True, color)
            width = max(400, txt_surface.get_width()+10)
            input_box.w = width
            input_box.centerx = WIDTH // 2
            pygame.draw.rect(screen, color, input_box, 2)
            screen.blit(txt_surface, (input_box.x+5, input_box.y+5))
            
            # Judul berubah sesuai mode
            title_str = "FREE TRIAL FOR 3 DAY" if license_mode == "TRIAL" else "PRODUCT ACTIVATION"
            title_surf = font_title.render(title_str, True, (255, 255, 255))
            screen.blit(title_surf, title_surf.get_rect(center=(WIDTH//2, HEIGHT//2 - 100)))
            
            msg_surf = font_msg.render(message, True, msg_color)
            screen.blit(msg_surf, msg_surf.get_rect(center=(WIDTH//2, HEIGHT//2 + 130)))
            
            pygame.display.flip()
            pygame.time.delay(1500)
            return True, text # Return True dan key yang baru saja aktif

        # === RENDER UI ===
        
        # Main Title
        main_title = font_main_title.render("SIMULASI SISTEM TATA SURYA", True, (255, 255, 255))
        screen.blit(main_title, main_title.get_rect(center=(WIDTH//2, HEIGHT//2 - 160)))

        # Sub Title (Dynamic)
        title_str = "FREE TRIAL FOR 3 DAY" if license_mode == "TRIAL" else "PRODUCT ACTIVATION"
        title_surf = font_title.render(title_str, True, (200, 200, 200))
        screen.blit(title_surf, title_surf.get_rect(center=(WIDTH//2, HEIGHT//2 - 100)))

        # Quote Elon Musk
        quote_text = "\"If The Universe is The Answer, then what is The Question ?\" - Elon Musk"
        quote_surf = font_quote.render(quote_text, True, (200, 200, 255)) 
        screen.blit(quote_surf, quote_surf.get_rect(center=(WIDTH//2, input_box.y - 30)))
        
        # Input Box
        if license_mode == "LIFETIME":
            txt_surface = font_input.render(text, True, color)
            width = max(400, txt_surface.get_width()+10)
            input_box.w = width
            input_box.centerx = WIDTH // 2
            
            s = pygame.Surface((input_box.w, input_box.h))
            s.set_alpha(100)
            s.fill((0, 0, 0))
            screen.blit(s, (input_box.x, input_box.y))
            
            screen.blit(txt_surface, (input_box.x+5, input_box.y+5))
            pygame.draw.rect(screen, color, input_box, 2)
        else:
            # Trial Mode: Hide Input or Show Text
            info_txt = font_msg.render("NO KEY REQUIRED FOR TRIAL", True, (150, 200, 150))
            screen.blit(info_txt, info_txt.get_rect(center=(WIDTH//2, input_box.centery)))
        
        # Render Tombol Trial
        screen.blit(trial_btn_surf, trial_btn_rect)
        
        # Message Area
        msg_surf = font_msg.render(message, True, msg_color)
        screen.blit(msg_surf, msg_surf.get_rect(center=(WIDTH//2, HEIGHT//2 + 130)))
        
        # Online Warning
        online_msg = "Anda harus terhubung ke internet untuk mengaktivasi serial number product keynya, harap online."
        online_surf = font_small.render(online_msg, True, (200, 200, 200))
        screen.blit(online_surf, online_surf.get_rect(center=(WIDTH//2, HEIGHT - 30)))
        
        # Activate Button
        pygame.draw.rect(screen, (0, 150, 0) if state != LicenseState.ACTIVATING else (100, 100, 100), btn_rect, border_radius=5)
        pygame.draw.rect(screen, (255, 255, 255), btn_rect, 2, border_radius=5)
        btn_txt = font_msg.render("ACTIVATE", True, (255, 255, 255))
        screen.blit(btn_txt, btn_txt.get_rect(center=btn_rect.center))
        
        pygame.display.flip()
        clock.tick(30)
    return False, None

# ==============================================================================

def main():
    pygame.init()
    try:
        pygame.scrap.init()
    except:
        pass

    global WIDTH, HEIGHT

    # --- SPECIAL HWID RESET (For Testing/Specific User) ---
    # HWID: 48751573395980
    if get_hwid() == "48751573395980":
        log("Special HWID detected: Resetting license state...")
        if os.path.exists("trial_history.dat"):
            try: os.remove("trial_history.dat")
            except: pass
        if os.path.exists(LICENSE_FILE):
            try: os.remove(LICENSE_FILE)
            except: pass
    # ------------------------------------------------------

    # Tidak perlu init screen besar dulu, karena Splash Screen akan buat sendiri
    # Tampilkan Splash Screen (Loading Box)
    show_splash_screen()

    # Re-init Main Window setelah splash selesai
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    log(f"window created {WIDTH}x{HEIGHT} flags=RESIZABLE")
    pygame.display.set_caption("Solar System Revolution Simulation (Licensed)")

    # Load existing key (untuk validasi tombol back)
    active_key = None
    is_trial_mode = False
    trial_start_time = 0.0
    
    if os.path.exists(LICENSE_FILE):
        try:
            with open(LICENSE_FILE, "r") as f:
                content = f.read().split("|")
                if len(content) >= 3:
                    active_key = content[2].strip()
                if content[0] == "TRIAL" and len(content) >= 4:
                    is_trial_mode = True
                    trial_start_time = float(content[3])
        except: pass

    # Variabel kontrol agar screen awal tidak muncul jika sudah ada lisensi,
    # kecuali user menekan "Back"
    first_run = True
    
    # Pesan startup (misal untuk expired trial)
    startup_msg = None

    # --- SESSION LOOP ---
    while True:
        # Cek Expiration Trial (Brute Force Check)
        is_trial_expired = False
        if os.path.exists(LICENSE_FILE):
            try:
                with open(LICENSE_FILE, "r") as f:
                    content = f.read().split("|")
                    # Format TRIAL: TRIAL|HWID|KEY|START_TIMESTAMP
                    if content[0] == "TRIAL" and len(content) >= 4:
                        start_time_chk = float(content[3])
                        elapsed = time.time() - start_time_chk
                        # 3 hari = 3 * 24 * 3600 seconds
                        if elapsed > (3 * 24 * 3600):
                            is_trial_expired = True
            except: pass
        
        if is_trial_expired:
            # Hapus lisensi, reset key
            try: os.remove(LICENSE_FILE)
            except: pass
            active_key = None
            is_trial_mode = False
            first_run = True # Force agar logic check_license_locally gagal (sebenarnya file sdh dihapus jd aman)
            startup_msg = "masa 3 day free trial anda sudah habis, ayok ke versi lifetime"
        
        # Jika Back ditekan (first_run False) ATAU File lisensi tidak ada: Tampilkan License Screen
        # Jika Start Up (first_run True) DAN File Lisensi Ada: Skip
        
        should_show_license = True
        if first_run and check_license_locally():
            should_show_license = False
        
        if should_show_license:
             # Pass active_key jika ada (untuk validasi ulang)
             # Pass startup_msg jika ada
             authorized, new_key = license_screen(screen, target_key=active_key, startup_message=startup_msg)
             if not authorized:
                 pygame.quit()
                 return
             active_key = new_key
             startup_msg = None # Reset pesan setelah berhasil masuk
             
             # Re-check mode after activation
             if os.path.exists(LICENSE_FILE):
                try:
                    with open(LICENSE_FILE, "r") as f:
                        content = f.read().split("|")
                        if content[0] == "TRIAL" and len(content) >= 4:
                            is_trial_mode = True
                            trial_start_time = float(content[3])
                        else:
                            is_trial_mode = False
                except: pass
        else:
             # File ada. Baca keynya jika belum dibaca.
             if not active_key:
                  try:
                      with open(LICENSE_FILE, "r") as f:
                          content = f.read().split("|")
                          if len(content) >= 3:
                              active_key = content[2].strip()
                          if content[0] == "TRIAL" and len(content) >= 4:
                                is_trial_mode = True
                                trial_start_time = float(content[3])
                          else:
                                is_trial_mode = False
                  except: pass
        
        first_run = False # Setelah sesi pertama, flag ini mati

        # Masuk Game Loop
        
        font = pygame.font.SysFont("arial", 16)
        small_font = pygame.font.SysFont("arial", 14)
        tooltip = Tooltip(pygame.font.SysFont("arial", 14))
        watermark_font = pygame.font.SysFont("arial", 12, italic=True)
        watermark_text = watermark_font.render("@emansipation", True, (255, 255, 255))
        watermark_shadow = watermark_font.render("@emansipation", True, (0, 0, 0))
        
        # Tombol Kembali / Reset License
        back_btn_font = pygame.font.SysFont("arial", 12, bold=True)
        back_btn_text = back_btn_font.render("<< RESET / LOGIN", True, (255, 100, 100))
        back_btn_rect = pygame.Rect(0, 0, 0, 0) # Akan dihitung saat draw
        
        overlay = PlanetOverlay(font)
        language_modal = None
        data_modal = None
        time_modal = None
        mars_modal = None
        blur = BlurLayer()
        clock = pygame.time.Clock()
        book_icon = load_book_icon(DATA_BUTTON_SIZE)

        sun = SimpleNamespace(name="Sun", color=(255, 215, 0), radius=SUN_DRAW_RADIUS)

        planets = [
            Planet("Mercury", (169, 169, 169), 60, 4, 88),
            Planet("Venus", (218, 165, 32), 90, 7, 225),
            Planet("Earth", (100, 149, 237), 120, 7, 365),
            Planet("Mars", (188, 39, 50), 150, 6, 687),
            Planet("Jupiter", (222, 184, 135), 220, 12, 4330),
            Planet("Saturn", (210, 180, 140), 260, 10, 10752),
            Planet("Uranus", (175, 238, 238), 300, 9, 30660),
            Planet("Neptune", (72, 61, 139), 340, 9, 59860),
        ]

        space = pymunk.Space()
        for p in planets:
            shape = pymunk.Circle(p.body, p.radius)
            space.add(p.body, shape)

        if USE_APPROX_ORBITS:
            apply_approx_orbits(planets)
        else:
            recalculate_orbits(planets)

        camera = Camera2D()
        speed_index = 1
        speed_multiplier = SPEED_OPTIONS[speed_index]
        show_keyboard_info = False
        keyboard_info_rect = None
        keyboard_button_color = list(KEYBOARD_BTN_INACTIVE)
        paused = False
        rotating = False
        sketch_mode = False 
        last_mouse_x = 0
        show_debug = False
        input_vec = Vector2()
        ui_state = UIState.RUNNING
        selected_planet = None
        pending_overlay = None
        fullscreen = False
        windowed_size = (WIDTH, HEIGHT)
        speed_rects = []
        angle_button_rects = []
        angle_focus = -1
        keyboard_button_rect = pygame.Rect(0, 0, 0, 0)
        language_button_rect = pygame.Rect(0, 0, 0, 0)
        data_button_rect = pygame.Rect(0, 0, 0, 0)
        time_info_button_rect = pygame.Rect(0, 0, 0, 0)
        play_rect = pygame.Rect(0, 0, 0, 0)
        pause_rect = pygame.Rect(0, 0, 0, 0)
        sketch_button_rect = pygame.Rect(0, 0, 0, 0) 
        start_x = button_y = 0
        lod_active = camera.zoom < LOD_ZOOM
        
        user_requested_back = False

        def recalc_ui():
            nonlocal speed_rects, angle_button_rects, keyboard_button_rect
            nonlocal play_rect, pause_rect, start_x, button_y, data_button_rect, time_info_button_rect
            nonlocal sketch_button_rect
            speed_rects = [pygame.Rect(10 + i * 55, 10, 50, 25) for i in range(len(SPEED_OPTIONS))]

            angle_button_rects = []
            x = 10
            y = 40
            for label in ANGLE_LABELS:
                w, _ = font.size(label)
                rect = pygame.Rect(x, y, w + 20, 25)
                angle_button_rects.append(rect)
                x += rect.width + 5

            keyboard_button_rect = pygame.Rect(10, y + 25 + 5, 170, 30)

            button_w, button_h, gap = 80, 30, 20
            total_w = button_w * 2 + gap
            start_x = WIDTH // 2 - total_w // 2
            button_y = HEIGHT - button_h - 10
            play_rect = pygame.Rect(start_x, button_y, button_w, button_h)
            pause_rect = pygame.Rect(start_x + button_w + gap, button_y, button_w, button_h)
            
            sketch_w = 120
            sketch_x = WIDTH // 2 - sketch_w // 2
            sketch_y = button_y - 40
            sketch_button_rect = pygame.Rect(sketch_x, sketch_y, sketch_w, 30)

            data_button_rect = pygame.Rect(
                WIDTH - DATA_BUTTON_SIZE - 10,
                HEIGHT - DATA_BUTTON_SIZE - 10,
                DATA_BUTTON_SIZE,
                DATA_BUTTON_SIZE,
            )
            time_info_button_rect = pygame.Rect(0, 0, 0, 0)

        recalc_ui()

        def change_language(lang):
            global CURRENT_LANG, ANGLE_LABELS
            CURRENT_LANG = lang
            ANGLE_LABELS = [t(k) for k in ANGLE_LABEL_KEYS]
            if USE_APPROX_ORBITS:
                apply_approx_orbits(planets)
            else:
                recalculate_orbits(planets)
            recalc_ui()

        def draw_watermark_and_back(surface):
            x = 10
            y = HEIGHT - watermark_text.get_height() - 10
            
            # Watermark
            if sketch_mode:
                black_wm = watermark_font.render("@emansipation", True, (0, 0, 0))
                surface.blit(black_wm, (x, y))
            else:
                surface.blit(watermark_shadow, (x + 1, y + 1))
                surface.blit(watermark_text, (x, y))
            
            # Tombol Back
            wm_w = watermark_text.get_width()
            nonlocal back_btn_rect
            btn_x = x + wm_w + 15
            back_btn_rect = pygame.Rect(btn_x, y - 2, back_btn_text.get_width() + 10, back_btn_text.get_height() + 4)
            
            # Draw button background (agak transparan merah)
            s = pygame.Surface((back_btn_rect.width, back_btn_rect.height), pygame.SRCALPHA)
            s.fill((100, 0, 0, 150))
            surface.blit(s, back_btn_rect.topleft)
            pygame.draw.rect(surface, (150, 50, 50), back_btn_rect, 1)
            
            surface.blit(back_btn_text, (btn_x + 5, y))

        def reset_view():
            camera.pos.update(0.0, 0.0)
            camera.rot = 0.0
            camera._update_cache()
            camera._zoom_k = 0.0
            log("reset view")

        def reset_simulation():
            nonlocal paused
            for p in planets:
                p.angle = 0.0
                p.elapsed = 0.0
                p.body.position = (p.orbit_radius, 0)
            paused = True
            log("simulation reset")

        def apply_angle(mode):
            camera.set_angle_mode(mode)
            reset_view()

        def draw_scene_to(surface, dt):
            nonlocal keyboard_button_color, keyboard_info_rect, speed_rects
            nonlocal input_vec, angle_button_rects, angle_focus, lod_active
            nonlocal language_button_rect, time_info_button_rect
            nonlocal sketch_button_rect
            
            bg_color = (255, 255, 255) if sketch_mode else (10, 10, 30)
            surface.fill(bg_color)
            
            draw_curvature(surface, camera, sketch_mode=sketch_mode)
            draw_orbits(surface, planets, camera, sketch_mode=sketch_mode)
            draw_distance_reference(surface, camera, small_font, sketch_mode=sketch_mode)
            
            sx, sy = camera.world_to_screen((0, 0))
            
            if sketch_mode:
                pygame.draw.circle(surface, (0, 0, 0), (sx, sy), int(SUN_DRAW_RADIUS * camera.zoom), 2)
            else:
                pygame.draw.circle(surface, (255, 215, 0), (sx, sy), int(SUN_DRAW_RADIUS * camera.zoom))

            planet_screen = [(sun, (sx, sy), int(SUN_DRAW_RADIUS * camera.zoom))]
            info_lines = []
            for pl in planets:
                if not paused:
                    x, y = pl.update(dt * speed_multiplier)
                else:
                    x, y = pl.body.position
                px, py = camera.world_to_screen((x, y))
                
                p_color = (0, 0, 0) if sketch_mode else pl.color
                text_color = (0, 0, 0) if sketch_mode else (255, 255, 255)
                
                if lod_active:
                    surface.fill(p_color, (px, py, 1, 1))
                    radius = 1
                else:
                    radius = max(1, int(pl.radius * camera.zoom))
                    if sketch_mode:
                        pygame.draw.circle(surface, (0,0,0), (px, py), radius, 1)
                    else:
                        pygame.draw.circle(surface, pl.color, (px, py), radius)
                    
                    label = font.render(pl.name, True, text_color)
                    label_rect = label.get_rect(center=(px, py - 15 * camera.zoom))
                    surface.blit(label, label_rect)
                info_lines.append(f"{pl.name}: {pl.elapsed:.1f}/{pl.period_seconds:.1f}s")
                planet_screen.append((pl, (px, py), radius))

            panel_width = 260
            panel_height = len(info_lines) * 18 + 10
            panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
            
            panel_bg = (200, 200, 200, 150) if sketch_mode else (0, 0, 0, 150)
            panel_text_col = (0, 0, 0) if sketch_mode else (255, 255, 255)
            
            panel.fill(panel_bg)
            for i, text in enumerate(info_lines):
                txt = font.render(text, True, panel_text_col)
                panel.blit(txt, (5, 5 + i * 18))
            panel_pos = (WIDTH - panel_width - 10, 10)
            surface.blit(panel, panel_pos)
            
            info_d = 18
            info_rect = pygame.Rect(panel_pos[0] + panel_width - info_d - 5, panel_pos[1] + 5, info_d, info_d)
            hover_info = info_rect.collidepoint(pygame.mouse.get_pos())
            
            btn_bg = (180, 180, 180) if hover_info else (255, 255, 255)
            pygame.draw.circle(surface, btn_bg, info_rect.center, info_d // 2)
            pygame.draw.circle(surface, (0, 0, 0), info_rect.center, info_d // 2, 2)
            i_txt = small_font.render("i", True, (0, 0, 0))
            surface.blit(i_txt, i_txt.get_rect(center=info_rect.center))
            time_info_button_rect = info_rect

            lbl = font.render(t("lang_button"), True, (0, 0, 0))
            bw = lbl.get_width() + 20
            bh = 25
            lang_rect = pygame.Rect(panel_pos[0], panel_pos[1] + panel_height + 5, bw, bh)
            pygame.draw.rect(surface, (200, 200, 200), lang_rect, border_radius=5)
            pygame.draw.rect(surface, (0, 0, 0), lang_rect, 1, border_radius=5)
            surface.blit(lbl, lbl.get_rect(center=lang_rect.center))
            language_button_rect = lang_rect

            speed_rects = draw_speed_panel(surface, font, speed_index)
            draw_angle_buttons(surface, font, angle_button_rects, angle_focus, camera.angle_mode)
            
            target = KEYBOARD_BTN_ACTIVE if show_keyboard_info else KEYBOARD_BTN_INACTIVE
            for i in range(3):
                keyboard_button_color[i] += (target[i] - keyboard_button_color[i]) * 0.1
            button_color = tuple(int(c) for c in keyboard_button_color)
            draw_keyboard_button(surface, font, keyboard_button_rect, button_color)
            
            if show_keyboard_info:
                overlay_pos = (10, keyboard_button_rect.bottom + 5)
                keyboard_info_rect = draw_keyboard_overlay(surface, font, overlay_pos)
            else:
                keyboard_info_rect = None
                
            draw_play_pause_buttons(surface, font, paused, play_rect, pause_rect)
            
            draw_sketch_button(surface, font, sketch_button_rect, sketch_mode)
            
            surface.blit(book_icon, data_button_rect.topleft)
            if data_button_rect.collidepoint(pygame.mouse.get_pos()):
                tooltip.draw(surface, t("sources_tooltip"), (data_button_rect.right, data_button_rect.centery), "right")
            
            draw_watermark_and_back(surface)
            
            # --- TRIAL TIMER ---
            if is_trial_mode:
                elapsed = time.time() - trial_start_time
                remaining = max(0, (3 * 24 * 3600) - elapsed)
                days = int(remaining // (24 * 3600))
                hours = int((remaining % (24 * 3600)) // 3600)
                mins = int((remaining % 3600) // 60)
                secs = int(remaining % 60)
                
                timer_str = f"TRIAL: {days}d {hours}h {mins}m {secs}s"
                timer_col = (255, 50, 50) if remaining < 3600 else (255, 200, 50) # Red if < 1 hour
                
                # Gunakan font agak besar
                timer_surf = font.render(timer_str, True, timer_col)
                # Tampilkan di tengah atas, sedikit di bawah area HUD (misal y=40)
                surface.blit(timer_surf, timer_surf.get_rect(midtop=(WIDTH // 2, 50)))
            # -------------------

            if show_debug:
                draw_debug_overlay(surface, camera, font, input_vec)
            return planet_screen

        planet_positions = []
        running = True
        while running:
            dt = clock.tick(60) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    pygame.quit()
                    sys.exit() # Full exit
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                    fullscreen = not fullscreen
                    if fullscreen:
                        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
                        log("F11 fullscreen")
                    else:
                        screen = pygame.display.set_mode(windowed_size, pygame.RESIZABLE)
                        WIDTH, HEIGHT = windowed_size
                        recalc_ui()
                        log("F11 windowed")
                elif event.type == pygame.VIDEORESIZE:
                    WIDTH, HEIGHT = event.size
                    if not fullscreen:
                        windowed_size = event.size
                    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN if fullscreen else pygame.RESIZABLE)
                    recalc_ui()
                    if ui_state == UIState.OVERLAY and overlay.planet:
                        overlay._rebuild()
                    elif ui_state == UIState.DATA_SOURCES and data_modal:
                        data_modal._build()
                    elif ui_state == UIState.TIME_INFO and time_modal:
                        time_modal._build()
                    elif ui_state == UIState.MARS_BIO and mars_modal:
                        # Rebuild if needed or let build handle it next open
                        pass
                elif ui_state == UIState.OVERLAY:
                    res = overlay.handle_event(event, [sun] + planets)
                    if res == "close":
                        ui_state = UIState.RUNNING
                        selected_planet = None
                    # Handler untuk poin-poin Mars Detail (1-6)
                    elif res and res.startswith("open_mars_detail_"):
                        try:
                            detail_idx = int(res.split("_")[-1])
                            bg_capture = screen.copy()
                            mars_modal = PlanetUniversalModal(font, planet_name=overlay.planet.name, config_id=detail_idx)
                            mars_modal.open(bg_capture)
                            ui_state = UIState.MARS_BIO
                        except ValueError:
                            pass
                    continue
                elif ui_state == UIState.MARS_BIO:
                    res = mars_modal.handle_event(event)
                    if res == "close":
                        ui_state = UIState.OVERLAY # Back to overlay
                        mars_modal = None
                    continue
                elif ui_state == UIState.LANG_MODAL:
                    res = language_modal.handle_event(event)
                    if res == "close":
                        ui_state = UIState.RUNNING
                        language_modal = None
                    elif res in ("id", "en"):
                        change_language(res)
                        ui_state = UIState.RUNNING
                        language_modal = None
                    continue
                elif ui_state == UIState.DATA_SOURCES:
                    res = data_modal.handle_event(event)
                    if res == "close":
                        ui_state = UIState.RUNNING
                        data_modal = None
                    continue
                elif ui_state == UIState.TIME_INFO:
                    res = time_modal.handle_event(event)
                    if res == "close":
                        ui_state = UIState.RUNNING
                        time_modal = None
                    continue
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    # Escape hanya menutup game loop ini, balik ke OS
                    running = False
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_BACKSPACE:
                    reset_simulation()
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    reset_view()
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
                    angle_focus = (angle_focus + 1) % len(ANGLE_MODES)
                elif event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if angle_focus != -1:
                        apply_angle(ANGLE_MODES[angle_focus])
                        angle_focus = -1
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_F2:
                    show_debug = not show_debug
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_F1:
                    camera_self_test()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    clicked = False
                    if play_rect.collidepoint(event.pos):
                        paused = False
                        clicked = True
                    elif pause_rect.collidepoint(event.pos):
                        paused = True
                        clicked = True
                    elif sketch_button_rect.collidepoint(event.pos):
                        sketch_mode = not sketch_mode
                        clicked = True
                    elif back_btn_rect.collidepoint(event.pos):
                        # TOMBOL BACK DITEKAN
                        clicked = True
                        user_requested_back = True
                        running = False # Break inner loop
                    else:
                        for i, rect in enumerate(speed_rects):
                            if rect.collidepoint(event.pos):
                                speed_index = i
                                speed_multiplier = SPEED_OPTIONS[i]
                                clicked = True
                                break
                        if not clicked:
                            for i, rect in enumerate(angle_button_rects):
                                if rect.collidepoint(event.pos):
                                    apply_angle(ANGLE_MODES[i])
                                    angle_focus = -1
                                    clicked = True
                                    break
                        if keyboard_button_rect.collidepoint(event.pos):
                            show_keyboard_info = not show_keyboard_info
                            clicked = True
                        elif language_button_rect.collidepoint(event.pos):
                            language_modal = LanguageModal(font)
                            language_modal.open(screen.copy())
                            ui_state = UIState.LANG_MODAL
                            clicked = True
                        elif time_info_button_rect.collidepoint(event.pos):
                            time_modal = TimeInfoModal(font)
                            time_modal.open(screen.copy())
                            ui_state = UIState.TIME_INFO
                            clicked = True
                        elif data_button_rect.collidepoint(event.pos):
                            data_modal = DataSourcesModal(font, small_font)
                            data_modal.open(screen.copy())
                            ui_state = UIState.DATA_SOURCES
                            clicked = True
                        elif show_keyboard_info and keyboard_info_rect and keyboard_info_rect.collidepoint(event.pos):
                            clicked = True
                    if not clicked:
                        for pl, (px, py), rad in planet_positions:
                            if (Vector2(event.pos) - Vector2(px, py)).length() <= rad:
                                pending_overlay = pl
                                break
                        if not pending_overlay:
                            rotating = True
                            last_mouse_x = event.pos[0]
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    rotating = False
                elif event.type == pygame.MOUSEMOTION and rotating:
                    dx = event.pos[0] - last_mouse_x
                    camera.rot += dx * 0.005
                    camera._update_cache()
                    last_mouse_x = event.pos[0]
                elif event.type == pygame.MOUSEWHEEL:
                    camera.adjust_zoom(math.log(1.1) * event.y)

            if ui_state == UIState.RUNNING:
                keys = pygame.key.get_pressed()
                if keys[pygame.K_LEFT]:
                    camera.rot -= 0.02
                    camera._update_cache()
                if keys[pygame.K_RIGHT]:
                    camera.rot += 0.02
                    camera._update_cache()
                if keys[pygame.K_UP]:
                    camera.adjust_zoom(math.log(1.01))
                if keys[pygame.K_DOWN]:
                    camera.adjust_zoom(-math.log(1.01))
                
                # FIX W-S-A-D (Screen-Relative Movement)
                move = Vector2(0, 0)
                if keys[pygame.K_w]: move.y += 1
                if keys[pygame.K_s]: move.y -= 1
                if keys[pygame.K_a]: move.x -= 1
                if keys[pygame.K_d]: move.x += 1

                if move.length_squared() > 0:
                    if DIAGONAL_NORMALIZE:
                        move = move.normalize()
                    
                    angle = -camera.rot
                    rot_move = move.rotate_rad(angle)
                    
                    speed_dt = PAN_SPEED_WORLD * dt
                    if PAN_SPEED_MODE == "screen":
                        speed_dt /= camera.zoom
                    
                    camera.pos += rot_move * speed_dt
                    input_vec = rot_move # For debug display

                new_lod = camera.zoom < LOD_ZOOM
                if new_lod != lod_active:
                    lod_active = new_lod
                    log("LOD mode on" if lod_active else "LOD mode off")

                planet_positions = draw_scene_to(screen, dt)

                mouse_pos = pygame.mouse.get_pos()
                hover = None
                for pl, (px, py), rad in planet_positions:
                    if (Vector2(mouse_pos) - Vector2(px, py)).length() <= rad:
                        hover = (pl, (px, py), rad)
                        break
                if hover:
                    hover_col = (0, 0, 0) if sketch_mode else (255, 255, 255)
                    pygame.draw.circle(screen, hover_col, hover[1], hover[2] + 4, 1)
                    tooltip.draw(screen, hover[0].name, hover[1])

                if pending_overlay:
                    blur.from_surface(screen.copy())
                    overlay.open(pending_overlay)
                    ui_state = UIState.OVERLAY
                    selected_planet = pending_overlay
                    pending_overlay = None

                pygame.display.flip()
            elif ui_state == UIState.OVERLAY:
                blur.draw(screen)
                overlay.draw(screen)
                pygame.display.flip()
            elif ui_state == UIState.MARS_BIO:
                mars_modal.draw(screen)
                pygame.display.flip()
            elif ui_state == UIState.LANG_MODAL:
                language_modal.draw(screen)
                pygame.display.flip()
            elif ui_state == UIState.DATA_SOURCES:
                data_modal.draw(screen)
                pygame.display.flip()
            elif ui_state == UIState.TIME_INFO:
                time_modal.draw(screen)
                pygame.display.flip()

        if user_requested_back:
            # Jika user tekan Back, loop akan ulang dari awal.
            # Karena flag first_run sudah False, maka di awal loop akan masuk ke pengecekan lisensi
            pass
        else:
            # Jika loop berhenti bukan karena back (misal Quit), maka exit
            break

    pygame.quit()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Solar System Simulation")
    parser.add_argument("--test-camera", action="store_true", help="run camera self-test and exit")
    args = parser.parse_args()
    if args.test_camera:
        camera_self_test()
    else:
        main()
