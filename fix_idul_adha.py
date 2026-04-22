import re

with open("masjid-al-hijrah-61 ( idcloudhost - tombol akses, page, & first fitur - Idul Adha Qurban ).py", "r") as f:
    content = f.read()

# Let's extract the current IDUL_ADHA_DASHBOARD_HTML to see what's inside it.
start_idx = content.find('IDUL_ADHA_DASHBOARD_HTML = """')
end_idx = content.find('"""\n\nHOME_HTML', start_idx)

idul_html = content[start_idx:end_idx]

print(idul_html)
