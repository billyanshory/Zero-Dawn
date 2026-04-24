import re

with open("masjid-al-hijrah-63 ( idcloudhost - others 5 fitur - Idul Adha Qurban ).py", "r") as f:
    content = f.read()

# Replace submitQurbanStats
new_submit = """
    async function submitQurbanStats(e) {
        if(e) e.preventDefault();
        const form = document.getElementById('admin-qurban-form');
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());

        try {
            const res = await fetch('/admin/qurban/stats', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': data.csrf_token
                },
                body: JSON.stringify(data)
            });
            if(!res.ok) {
                let errText = "Gagal menyimpan data";
                try {
                    const errJson = await res.json();
                    errText = errJson.error || errText;
                } catch(parseErr) {}
                throw new Error(errText);
            }
            const result = await res.json();
            if(result.success) {
                alert("Data berhasil disimpan");
                fetchStats();
            } else {
                throw new Error(result.error || "Gagal menyimpan data");
            }
        } catch(err) {
            alert(err.message);
        }
    }
"""
content = re.sub(r"async function submitQurbanStats\(e\) \{.*?\}(?=\s*// Initial fetch)", new_submit.strip() + "\n", content, flags=re.DOTALL)


# Replace fetchStats (the public polling loop)
new_fetch_stats = """
    async function fetchStats() {
        try {
            const res = await fetch('/api/qurban/stats');
            if(!res.ok) {
                let errText = "Terjadi kesalahan saat menghubungi server. Mencoba kembali...";
                try {
                    const errJson = await res.json();
                    errText = errJson.error || errText;
                } catch(parseErr) {}
                throw new Error(errText);
            }
            const data = await res.json();

            // Hide loading/error, show grid
            document.getElementById('loading-state').classList.add('hidden');
            document.getElementById('error-state').classList.add('hidden');
            document.getElementById('dashboard-grid').classList.remove('hidden');

            // Update stats
            document.getElementById('val-sapi').innerText = data.total_cattle;
            document.getElementById('val-kambing').innerText = data.total_goat;
            document.getElementById('val-meat').innerText = parseFloat(data.total_meat_weight_kg).toLocaleString('id-ID');
            document.getElementById('val-packages-prepared').innerText = data.total_packages_prepared.toLocaleString('id-ID');
            document.getElementById('val-packages-distributed').innerText = data.total_packages_distributed.toLocaleString('id-ID');

            // Update admin inputs if they exist
            const inCattle = document.getElementById('input-cattle');
            if(inCattle && document.activeElement !== inCattle) inCattle.value = data.total_cattle;

            const inGoat = document.getElementById('input-goat');
            if(inGoat && document.activeElement !== inGoat) inGoat.value = data.total_goat;

            const inMeat = document.getElementById('input-meat');
            if(inMeat && document.activeElement !== inMeat) inMeat.value = data.total_meat_weight_kg;

            const inPrep = document.getElementById('input-packages-prep');
            if(inPrep && document.activeElement !== inPrep) inPrep.value = data.total_packages_prepared;

            const inDist = document.getElementById('input-packages-dist');
            if(inDist && document.activeElement !== inDist) inDist.value = data.total_packages_distributed;

            // Progress Bar Logic
            let pct = 0;
            if (data.total_packages_prepared > 0) {
                pct = Math.round((data.total_packages_distributed / data.total_packages_prepared) * 100);
            }
            if (pct > 100) pct = 100;

            document.getElementById('progress-bar').style.width = pct + '%';
            document.getElementById('val-progress-pct').innerText = pct + '%';

            // Sync time
            const now = new Date();
            document.getElementById('sync-time').innerText = now.toLocaleTimeString('id-ID', {hour12: false});

        } catch(e) {
            console.error('Fetch error:', e);
            document.getElementById('loading-state').classList.add('hidden');
            document.getElementById('dashboard-grid').classList.add('hidden');

            const errorState = document.getElementById('error-state');
            errorState.classList.remove('hidden');
            const p = errorState.querySelector('p');
            if(p) p.innerText = e.message;
        }
    }
"""

content = re.sub(r"async function fetchStats\(\) \{.*?\}(?=\s*// Initial fetch)", new_fetch_stats.strip() + "\n", content, flags=re.DOTALL)


# Replace generatePin and openPinListModal
new_pin_js = """
                async function generatePin() {
                    const name = document.getElementById('shohibul_name').value;
                    const type = document.getElementById('animal_type').value;
                    if(!name) { alert("Nama Shohibul harus diisi"); return; }

                    try {
                        const res = await fetch('/api/qurban/shohibul/generate_pin', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({name: name, type: type})
                        });
                        if(!res.ok) {
                            let errText = "Gagal membuat PIN";
                            try { const errJson = await res.json(); errText = errJson.error || errText; } catch(e) {}
                            throw new Error(errText);
                        }
                        const data = await res.json();
                        if(data.success) {
                            document.getElementById('generated-pin-text').innerText = data.pin;
                            document.getElementById('generated-name-text').innerText = name;
                            document.getElementById('new-pin-display').classList.remove('hidden');
                            document.getElementById('shohibul_name').value = '';
                        } else {
                            throw new Error(data.error || "Gagal membuat PIN");
                        }
                    } catch(e) {
                        alert(e.message);
                    }
                }

                function closePinListModal() {
                    document.getElementById('modal-pin-list').classList.add('hidden');
                }

                async function openPinListModal() {
                    document.getElementById('modal-pin-list').classList.remove('hidden');
                    const tbody = document.getElementById('pin-list-tbody');
                    tbody.innerHTML = '<tr><td colspan="5" class="p-4 text-center">Memuat data...</td></tr>';

                    try {
                        const res = await fetch('/api/qurban/shohibul/list_pins');
                        if(!res.ok) {
                            let errText = "Gagal memuat data";
                            try { const errJson = await res.json(); errText = errJson.error || errText; } catch(e) {}
                            throw new Error(errText);
                        }
                        const data = await res.json();
                        if(data.success) {
                            if(data.pins.length === 0) {
                                tbody.innerHTML = '<tr><td colspan="5" class="p-4 text-center text-gray-500">Belum ada PIN.</td></tr>';
                                return;
                            }
                            tbody.innerHTML = data.pins.map(p => `
                                <tr class="hover:bg-gray-50">
                                    <td class="p-3 font-mono font-bold text-red-700">${p.pin}</td>
                                    <td class="p-3">${p.name}</td>
                                    <td class="p-3">${p.type}</td>
                                    <td class="p-3"><span class="bg-gray-100 px-2 py-1 rounded text-xs">${p.status}</span></td>
                                    <td class="p-3 text-xs text-gray-500">...</td>
                                </tr>
                            `).join('');
                        } else {
                            throw new Error(data.error || "Gagal memuat data");
                        }
                    } catch(e) {
                        tbody.innerHTML = `<tr><td colspan="5" class="p-4 text-center text-red-500">${e.message}</td></tr>`;
                    }
                }
"""

content = re.sub(r"async function generatePin\(\) \{.*?function closePinListModal.*?async function openPinListModal\(\) \{.*?\}\s*(?=</script>)", new_pin_js.strip() + "\n            ", content, flags=re.DOTALL)


# Replace generateKupon and openKuponListModal
new_kupon_js = """
                async function loadSlots() {
                    try {
                        const res = await fetch('/api/qurban/pembagian/slots');
                        if(!res.ok) throw new Error('Gagal memuat slot');
                        const data = await res.json();
                        if(data.success) {
                            const select = document.getElementById('slot_id');
                            if(data.slots.length === 0) {
                                select.innerHTML = '<option value="">Belum ada slot dikonfigurasi</option>';
                            } else {
                                select.innerHTML = data.slots.map(s => `<option value="${s.id}">${s.rt} (${s.time})</option>`).join('');
                            }
                        }
                    } catch(e) {
                        console.error('Failed to load slots', e);
                    }
                }

                async function generateKupon() {
                    const nik = document.getElementById('warga_nik').value;
                    const slot_id = document.getElementById('slot_id').value;
                    if(!nik || nik.length !== 16) { alert("NIK harus 16 digit angka"); return; }
                    if(!slot_id) { alert("Pilih slot RT"); return; }

                    try {
                        const res = await fetch('/api/qurban/pembagian/generate_kupon', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({nik: nik, slot_id: slot_id})
                        });
                        if(!res.ok) {
                            let errText = "Gagal membuat Kupon";
                            try { const errJson = await res.json(); errText = errJson.error || errText; } catch(e) {}
                            throw new Error(errText);
                        }
                        const data = await res.json();
                        if(data.success) {
                            document.getElementById('generated-kupon-text').innerText = data.kupon;
                            document.getElementById('generated-nik-text').innerText = nik;
                            document.getElementById('new-kupon-display').classList.remove('hidden');
                            document.getElementById('warga_nik').value = '';
                        } else {
                            throw new Error(data.error || "Gagal membuat Kupon");
                        }
                    } catch(e) {
                        alert(e.message);
                    }
                }

                function closeKuponListModal() {
                    document.getElementById('modal-kupon-list').classList.add('hidden');
                }

                async function openKuponListModal() {
                    document.getElementById('modal-kupon-list').classList.remove('hidden');
                    const tbody = document.getElementById('kupon-list-tbody');
                    tbody.innerHTML = '<tr><td colspan="4" class="p-4 text-center">Memuat data...</td></tr>';

                    try {
                        const res = await fetch('/api/qurban/pembagian/list_kupons');
                        if(!res.ok) {
                            let errText = "Gagal memuat data";
                            try { const errJson = await res.json(); errText = errJson.error || errText; } catch(e) {}
                            throw new Error(errText);
                        }
                        const data = await res.json();
                        if(data.success) {
                            if(data.kupons.length === 0) {
                                tbody.innerHTML = '<tr><td colspan="4" class="p-4 text-center text-gray-500">Belum ada Kupon.</td></tr>';
                                return;
                            }
                            tbody.innerHTML = data.kupons.map(k => `
                                <tr class="hover:bg-gray-50">
                                    <td class="p-3 font-mono font-bold text-[#D4A017] uppercase">${k.kupon}</td>
                                    <td class="p-3">${k.nik}</td>
                                    <td class="p-3">${k.slot}</td>
                                    <td class="p-3"><span class="bg-gray-100 px-2 py-1 rounded text-xs">${k.status}</span></td>
                                </tr>
                            `).join('');
                        } else {
                            throw new Error(data.error || "Gagal memuat data");
                        }
                    } catch(e) {
                        tbody.innerHTML = `<tr><td colspan="4" class="p-4 text-center text-red-500">${e.message}</td></tr>`;
                    }
                }
"""

content = re.sub(r"async function loadSlots\(\) \{.*?function closeKuponListModal.*?async function openKuponListModal\(\) \{.*?\}\s*(?=// Load slots if admin)", new_kupon_js.strip() + "\n                \n                ", content, flags=re.DOTALL)


with open("masjid-al-hijrah-63 ( idcloudhost - others 5 fitur - Idul Adha Qurban ).py", "w") as f:
    f.write(content)
