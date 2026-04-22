with open("masjid-al-hijrah-61 ( idcloudhost - tombol akses, page, & first fitur - Idul Adha Qurban ).py", "r") as f:
    content = f.read()

start = content.find("<!-- LEFT COLUMN: WELCOME (Desktop Only) -->")
end = content.find("<!-- RIGHT COLUMN: PRAYER CARD & RAMADHAN BANNER -->", start)
print(content[start:end])
