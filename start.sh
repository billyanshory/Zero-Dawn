# start fake redis instead of real redis server, just to verify it boots without syntax errors
sed -i 's/import fakeredis as redis/import redis/g' sekolah_luar_biasa.py
python -c "import py_compile; py_compile.compile('sekolah_luar_biasa.py')"
