import re

with open("backup.py", "r", encoding="utf-8") as f:
    text = f.read()

# Let's count how many variables we have to move
vars = [
    'STYLES_HTML',
    'BASE_LAYOUT',
    'FITUR_MASJID_HTML',
    'HOME_HTML',
    'RAMADHAN_STYLES',
    'RAMADHAN_DASHBOARD_HTML',
    'IRMA_STYLES',
    'IRMA_DASHBOARD_HTML'
]

# We need to find the start and end of these.
