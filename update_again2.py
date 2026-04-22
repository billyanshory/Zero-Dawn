import re

with open("masjid-al-hijrah-61 ( idcloudhost - tombol akses, page, & first fitur - Idul Adha Qurban ).py", "r") as f:
    content = f.read()

# Let's see the entire IDUL_ADHA_DASHBOARD_HTML before my change (by using git checkout temporarily or just logic)
# Actually, I can just rewrite the IDUL_ADHA_DASHBOARD_HTML entirely based on the prompt's exact instructions!
# Prompt:
# 1. Desktop: dual panel layout. Left: Greeting & 2 buttons. Right: Prayer Card.
# 2. Mobile: Top: Prayer card. Below it: Menu Qurban grid (which has Absen Panitia, Laporan Qurban, etc).
# 3. No overlapping elements, flexbox/grid transitions flawless.

# If we look at HOME_HTML, it does exactly this:
# Desktop: Left Welcome, Right Prayer Card.
# Mobile: Welcome is hidden (`hidden md:block`). Prayer Card is visible.
# Below that header, there's `<!-- MAIN GRID MENU -->`.

# So for IDUL_ADHA_DASHBOARD_HTML, we want:
# Header:
# - Desktop: Left Welcome, Right Prayer Card.
# - Mobile: Prayer Card (Welcome hidden).
# Body:
# - Menu Qurban Grid spanning full width (or aligned properly) below the header.

# So we can remove the old Prayer Card that was next to the Menu Grid in the old layout.
