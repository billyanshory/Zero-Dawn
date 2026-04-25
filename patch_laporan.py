import re

with open("masjid-al-hijrah-64 ( idcloudhost - fixing 4 fitur - Idul Adha Qurban ).py", "r") as f:
    content = f.read()

# Add submitQurbanStats function
js_search = """    // Initial fetch
    fetchStats();"""

js_replace = """    async function submitQurbanStats(event) {
        event.preventDefault();

        const cattle = parseInt(document.getElementById('input-cattle').value) || 0;
        const goat = parseInt(document.getElementById('input-goat').value) || 0;
        const meat = parseFloat(document.getElementById('input-meat').value) || 0;
        const prep = parseInt(document.getElementById('input-packages-prep').value) || 0;
        const dist = parseInt(document.getElementById('input-packages-dist').value) || 0;

        const payload = {
            total_cattle: cattle,
            total_goat: goat,
            total_meat_weight_kg: meat,
            total_packages_prepared: prep,
            total_packages_distributed: dist
        };

        try {
            const res = await fetch('/admin/qurban/stats', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            });
            if(!res.ok) {
                let errText = "Gagal menyimpan data";
                try { const errJson = await res.json(); errText = errJson.error || errText; } catch(e) {}
                throw new Error(errText);
            }
            const data = await res.json();
            if(data.success) {
                alert("Data berhasil disimpan!");
                fetchStats();
            } else {
                throw new Error(data.error || "Gagal menyimpan data");
            }
        } catch(e) {
            alert(e.message);
        }
    }

    // Initial fetch
    fetchStats();"""

content = content.replace(js_search, js_replace)

# Fix IDUL_ADHA_PEMBAGIAN_ADMIN_HTML button
btn_search = """                <button type="button" onclick="submitQurbanStats(event)" class="w-full bg-[#1B4332] text-white font-bold py-4 mt-2 rounded-xl hover:bg-[#153426] transition shadow-lg flex items-center justify-center gap-2">
                    <i class="fas fa-plus"></i> Buat Slot Alokasi
                </button>"""

btn_replace = """                <button type="submit" class="w-full bg-[#1B4332] text-white font-bold py-4 mt-2 rounded-xl hover:bg-[#153426] transition shadow-lg flex items-center justify-center gap-2">
                    <i class="fas fa-plus"></i> Buat Slot Alokasi
                </button>"""

content = content.replace(btn_search, btn_replace)

with open("masjid-al-hijrah-64 ( idcloudhost - fixing 4 fitur - Idul Adha Qurban ).py", "w") as f:
    f.write(content)
