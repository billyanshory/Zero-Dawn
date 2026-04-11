import sys

filename = "sekolah-luar-biasa-69 ( idcloudhost - debugging - waktu, save data, warna tab, jadwal medis error, tambah kamus, json file kamus, api modul  - Opus 4.6 ).py"

with open("backup.py", 'r') as f:
    lines = f.readlines()

def get_index(lines, sub, start=0):
    for i in range(start, len(lines)):
        if sub in lines[i]:
            return i
    return -1

# 1. modal-infaq (HTML block)
start = get_index(lines, '<div id="modal-infaq"')
end = get_index(lines, '<!-- PORTAL MASUK & REGISTRASI MODAL -->', start)
if start != -1 and end != -1:
    lines = lines[:start] + lines[end:]

# JS adjustInfaqTheme
start = get_index(lines, 'function adjustInfaqTheme()')
end = get_index(lines, 'function closeModal(id)', start)
if start != -1 and end != -1:
    lines = lines[:start] + lines[end:]

# JS formatBankDisplay
start = get_index(lines, 'function formatBankDisplay(id)')
end = start
if start != -1:
    while '</script>' not in lines[end] and 'dataset.formatted =' not in lines[end]:
        end += 1
    # include up to the closing brace
    while '}' not in lines[end]:
        end += 1
    lines = lines[:start] + lines[end+1:]

# JS openModal infaq logic
start = get_index(lines, "if(id === 'modal-infaq') {")
end = start
if start != -1:
    while '}' not in lines[end]:
        end += 1
    lines = lines[:start] + lines[end+1:]

# JS triggerInfaqWA global
start = get_index(lines, 'function triggerInfaqWA()')
end = start
if start != -1:
    while end+1 < len(lines) and 'function ' not in lines[end+1] and 'async function ' not in lines[end+1]:
        end += 1
    lines = lines[:start] + lines[end+1:]

# 2. Routes
# /donate route
start = get_index(lines, "@app.route('/donate', methods=['GET', 'POST'])")
end = get_index(lines, "@app.route('/emergency')", start)
if start != -1 and end != -1:
    lines = lines[:start] + lines[end:]

# /emergency route
start = get_index(lines, "@app.route('/emergency')")
end = get_index(lines, "@app.route('/uploads/<path:filename>')", start)
if start != -1 and end != -1:
    lines = lines[:start] + lines[end:]

# /donate/update
start = get_index(lines, "@app.route('/donate/update', methods=['POST'])")
end = get_index(lines, "@app.route('/jadwal')", start)
if start != -1 and end != -1:
    lines = lines[:start] + lines[end:]

# 3. Ramadhan and IRMA Dashboards
start = get_index(lines, "# --- RAMADHAN SPECIAL FEATURES ---")
end = get_index(lines, "# --- DASHBOARD GURU ROUTES ---", start)
if start != -1 and end != -1:
    lines = lines[:start] + lines[end:]

# /ramadhan route
start = get_index(lines, "@app.route('/ramadhan')")
end = get_index(lines, "@app.route('/guru/tantrum', methods=['POST'])", start)
if start != -1 and end != -1:
    lines = lines[:start] + lines[end:]

# Other Ramadhan/IRMA leftovers
def remove_line(sub):
    global lines
    idx = get_index(lines, sub)
    if idx != -1:
        lines = lines[:idx] + lines[idx+1:]

remove_line("# --- RESTORED RAMADHAN ROUTES ---")
remove_line("# --- IRMA ROUTES ---")
remove_line("# --- IRMA DASHBOARD ASSETS ---")

# Ramadhan Mode CSS
start = get_index(lines, "/* RAMADHAN MODE UTILS */")
if start != -1:
    end = start
    while '"""' not in lines[end] and '/* HIGHLIGHT CURRENT PAGE IN BOTTOM NAV */' not in lines[end]:
        end += 1
    # Replace with just the closure if it's the end of string
    if '"""' in lines[end]:
        lines = lines[:start] + ['"""\n'] + lines[end+1:]
    else:
        lines = lines[:start] + lines[end:]

# Remove {{ 'ramadhan-mode' ... }}
for i in range(len(lines)):
    lines[i] = lines[i].replace("{{ 'ramadhan-mode' if 'ramadhan' in request.path else '' }}", "")

# 4. Hijri logic
remove_line('id="hijri-date"')
remove_line('fetchHijri();')
remove_line('<p id="hijri-date" class="text-[10px] text-gray-500 font-bold mb-0.5 tracking-wider uppercase flex items-center justify-end gap-1"><i class="fas fa-moon text-emerald-500"></i> Memuat Hijriah...</p>\n')

start = get_index(lines, "function fetchHijri()")
end = get_index(lines, "function updateDate()", start) # more reliable stop point
if start != -1 and end != -1:
    lines = lines[:start] + lines[end:]

# 5. Ramadhan Banner
start = get_index(lines, '<a href="/ramadhan"')
if start != -1:
    end = start
    while not ('</a>' in lines[end] and '<a href="/ramadhan"' not in lines[end]):
        end += 1
    lines = lines[:start] + lines[end+1:]

# Join back to string
content = "".join(lines)

# Rename PRAYER CARD to KARTU PROFIL & PAPAN KOMUNIKASI
content = content.replace("<!-- RIGHT COLUMN: PRAYER CARD & RAMADHAN BANNER -->", "<!-- RIGHT COLUMN: KARTU PROFIL & PAPAN KOMUNIKASI -->")

# PWA & Branding replace
content = content.replace('"Masjid Al Hijrah"', '"Sekolah Luar Biasa"')
content = content.replace('"Aplikasi Masjid Al Hijrah Samarinda"', '"Aplikasi SLB Waktu Samarinda"')
content = content.replace('logomasjidalhijrah.png', 'logoslb.png')
content = content.replace('al-hijrah-v1', 'slb-v1')
content = content.replace('"Al Hijrah"', '"SLB"')

# WhatsApp message update
content = content.replace('Assalamualaikum, Selamat ${time}, maaf mengganggu waktunya Pak ya... Saya butuh bantuan darurat.', 'Halo, Selamat ${time}, saya butuh bantuan darurat terkait SLB Waktu Samarinda.')

# Calculator ID renames
content = content.replace('result-waris', 'result-imt')
content = content.replace('result-zakat', 'result-sensory')
content = content.replace('result-tahajjud', 'result-auditori')
content = content.replace('result-khatam', 'result-iq')
content = content.replace('result-fidyah', 'result-motorik')
content = content.replace('result-hijri', 'result-diet')

# Calculator Data Dict renames
content = content.replace('"waris": [', '"imt": [')
content = content.replace('"zakat": [', '"sensory": [')
content = content.replace('"tahajjud": [', '"auditori": [')
content = content.replace('"khatam": [', '"iq": [')
content = content.replace('"fidyah": [', '"motorik": [')
content = content.replace('"hijri": [', '"diet": [')

with open(filename, 'w') as f:
    f.write(content)
