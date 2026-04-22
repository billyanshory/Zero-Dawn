with open("masjid-al-hijrah-61 ( idcloudhost - tombol akses, page, & first fitur - Idul Adha Qurban ).py", "r") as f:
    content = f.read()

start = content.find("<!-- DESKTOP SPLIT HEADER -->")
end = content.find("<!-- MAIN CONTENT -->", start)
print(content[start:end])
