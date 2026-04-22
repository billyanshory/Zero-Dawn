sed -i 's/app.run(debug=True, port=5000)/#app.run(debug=True, port=5000)/' "masjid-al-hijrah-62 ( idcloudhost - fixing lay out - Idul Adha Qurban ).py"
cp "masjid-al-hijrah-62 ( idcloudhost - fixing lay out - Idul Adha Qurban ).py" app.py
python test_endpoints.py
