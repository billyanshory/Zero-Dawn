import re
with open("sekolah-luar-biasa-90 ( idcloudhost - Nineteenth Layer of Quality Control - Data Privacy & Compliance (SLB-Specific) - v.89 - Opus 4.7 Ad. Think ).py", "r") as f:
    text = f.read()

# Replace Giphy with local for SIBI gifs in seed_sibi_words
search_giphy1 = """                ("aku", "https://media.giphy.com/media/l41lFj8af0LC6wcxs/giphy.gif"),
                ("ingin", "https://media.giphy.com/media/xT9IgG50Fb7Mi0prBC/giphy.gif"),
                ("makan", "https://media.giphy.com/media/3o7bu3XilJ5BOiSGic/giphy.gif"),
                ("minum", "https://media.giphy.com/media/l0HlHJDqLkcCHVz3y/giphy.gif"),
                ("tidur", "https://media.giphy.com/media/3o6Zt481isN3u/giphy.gif"),
                ("shalat", "https://media.giphy.com/media/l0MYt5jPR6QX5pnqM/giphy.gif"),
                ("wudhu", "https://media.giphy.com/media/l0MYt5jPR6QX5pnqM/giphy.gif"),"""

replace_giphy1 = """                ("aku", "/static/sibi/aku.gif"),
                ("ingin", "/static/sibi/ingin.gif"),
                ("makan", "/static/sibi/makan.gif"),
                ("minum", "/static/sibi/minum.gif"),
                ("tidur", "/static/sibi/tidur.gif"),
                ("shalat", "/static/sibi/shalat.gif"),
                ("wudhu", "/static/sibi/wudhu.gif"),"""

# Replace Giphy for sholat/adzan in dashboard
search_giphy2 = """             "sholat": "https://media.giphy.com/media/3o7TKMt1VVNkHV2PaE/giphy.gif",
             "adzan": "https://media.giphy.com/media/3o7TKMt1VVNkHV2PaE/giphy.gif" """

replace_giphy2 = """             "sholat": "/static/sibi/sholat.gif",
             "adzan": "/static/sibi/adzan.gif" """

# Remove Twemoji prefetch completely since we don't have access to internet to download it and it's not strictly necessary. Let's look at the prefetch.
search_twemoji = """                if not r.set("slb_emoji_prefetch", "1", nx=True, ex=86400):
                    return

            hex_codes = ['1f441', '1f442', '1f3c3', '1f590', '1f3af', '1f5e3', '2753']
            for icon_hex in hex_codes:
                file_path = os.path.join(emoji_dir, f"{icon_hex}.png")
                if not os.path.exists(file_path):
                    url = f"https://cdnjs.cloudflare.com/ajax/libs/twemoji/14.0.2/72x72/{icon_hex}.png"
                    try:
                        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=(3, 10))
                        if response.status_code == 200:
                            with open(file_path, 'wb') as out_f:
                                out_f.write(response.content)
                    except requests.RequestException:
                        app.logger.warning(f"Failed to prefetch emoji {icon_hex}", exc_info=True)"""

replace_twemoji = """                pass"""

if search_giphy1 in text:
    text = text.replace(search_giphy1, replace_giphy1)
if search_giphy2 in text:
    text = text.replace(search_giphy2, replace_giphy2)
if search_twemoji in text:
    text = text.replace(search_twemoji, replace_twemoji)

# Update Kebijakan Privasi
search_privasi = """    <p><strong>Pengungkapan ke Pihak Ketiga:</strong> Kami menggunakan layanan pihak ketiga yang mungkin menerima sebagian data IP/User-Agent Anda:</p>
    <ul>
        <li><strong>pmpk.kemdikbud.go.id:</strong> Pencarian SIBI lokal Indonesia.</li>
        <li><strong>equran.id & aladhan.com:</strong> Data jadwal sholat & Al-Quran.</li>
        <li><strong>YouTube:</strong> Video pembelajaran disematkan (embed).</li>
    </ul>"""

replace_privasi = """    <h3>Aset CDN Lintas Yurisdiksi</h3>
    <ul>
        <li><strong>aladhan.com:</strong> API Jadwal Sholat (Lintas batas, namun minim PII).</li>
        <li><strong>youtube.com:</strong> Video pembelajaran (embed lintas batas).</li>
    </ul>
    <h3>Penyedia Pihak Ketiga Lintas Yurisdiksi</h3>
    <p>Dependensi CDN berikut telah dihapus dan sepenuhnya dikelola lokal (Self-hosted) untuk kepatuhan privasi:</p>
    <ul>
        <li>FontAwesome (CDN dihapus)</li>
        <li>Tailwind JIT (CDN dihapus)</li>
        <li>Twemoji & Giphy (Aset dialihkan ke lokal)</li>
    </ul>
    <p><strong>Pengungkapan ke Pihak Ketiga:</strong> Kami menggunakan layanan pihak ketiga yang mungkin menerima sebagian data IP/User-Agent Anda:</p>
    <ul>
        <li><strong>pmpk.kemdikbud.go.id:</strong> Pencarian SIBI lokal Indonesia.</li>
        <li><strong>equran.id:</strong> Data jadwal sholat & Al-Quran.</li>
    </ul>"""

if search_privasi in text:
    text = text.replace(search_privasi, replace_privasi)

with open("sekolah-luar-biasa-90 ( idcloudhost - Nineteenth Layer of Quality Control - Data Privacy & Compliance (SLB-Specific) - v.89 - Opus 4.7 Ad. Think ).py", "w") as f:
    f.write(text)

print("Success")
