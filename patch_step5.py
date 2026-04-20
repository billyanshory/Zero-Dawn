with open("sekolah-luar-biasa-90 ( idcloudhost - Nineteenth Layer of Quality Control - Data Privacy & Compliance (SLB-Specific) - v.89 - Opus 4.7 Ad. Think ).py", "r") as f:
    text = f.read()

search = """                    <div id="siswa-dropdown-container" class="hidden">
                        <label for="reg-anak" class="block text-xs font-bold text-gray-500 mb-1">Pilih Anak (Siswa)</label>
                                        <select id="reg-anak" name="anak_id" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500">
                            <!-- Injected dynamically or rendered via template -->
                            <option value="">Pilih Siswa...</option>
                            {% for s in list_siswa %}
                            <option value="{{ s['id'] }}">{{ s['nama'] }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <button type="submit" class="w-full bg-blue-500 text-white font-bold py-3 rounded-xl shadow-lg hover:bg-blue-600 transition">Daftar</button>
                </form>"""

replace = """                    <div id="siswa-dropdown-container" class="hidden">
                        <label for="reg-anak" class="block text-xs font-bold text-gray-500 mb-1">Pilih Anak (Siswa)</label>
                                        <select id="reg-anak" name="anak_id" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500">
                            <!-- Injected dynamically or rendered via template -->
                            <option value="">Pilih Siswa...</option>
                            {% for s in list_siswa %}
                            <option value="{{ s['id'] }}">{{ s['nama'] }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div>
                        <label for="reg-tgl-lahir" class="block text-xs font-bold text-gray-500 mb-1">Tanggal Lahir</label>
                        <input id="reg-tgl-lahir" type="date" name="tanggal_lahir" class="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm">
                        <p class="text-xs text-gray-400 mt-1">Wajib bagi Orang Tua (&ge;18 tahun).</p>
                    </div>
                    <div class="flex items-start gap-2 pt-2">
                        <input id="reg-consent" type="checkbox" name="persetujuan_privasi" value="v1.0" required class="mt-1"/>
                        <label for="reg-consent" class="text-xs text-gray-600 leading-relaxed">Saya selaku wali anak berusia di bawah 18 tahun, memberikan persetujuan yang bebas, spesifik, dan jelas untuk pemrosesan Data Pribadi anak saya sebagaimana dijelaskan dalam <a href="/kebijakan-privasi" target="_blank" class="text-emerald-600 underline">Kebijakan Privasi v1.0</a>, termasuk kategori Data Pribadi Spesifik (kesehatan, hambatan) sesuai UU PDP Art. 20 dan 26.</label>
                    </div>
                    <button type="submit" class="w-full bg-blue-500 text-white font-bold py-3 rounded-xl shadow-lg hover:bg-blue-600 transition">Daftar</button>
                </form>"""

if search in text:
    text = text.replace(search, replace)
    with open("sekolah-luar-biasa-90 ( idcloudhost - Nineteenth Layer of Quality Control - Data Privacy & Compliance (SLB-Specific) - v.89 - Opus 4.7 Ad. Think ).py", "w") as f:
        f.write(text)
    print("Success")
else:
    print("Search string not found")
