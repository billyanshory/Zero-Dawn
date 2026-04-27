import re

with open("masjid-al-hijrah-65 - alternate - ( idcloudhost - fixing 4 fitur - Idul Adha Qurban - Second Effort).py", "r") as f:
    content = f.read()

# Replace Edit form and Action buttons with AJAX methods in Peta Distribusi
old_buttons = """                {% if is_admin %}
                    {% if rt.status == 'Menunggu' %}
                    <form action="/idul-adha/peta-distribusi/update_status" method="POST">
                        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                        <input type="hidden" name="rt_id" value="{{ rt.id }}">
                        <input type="hidden" name="status" value="Diserahkan">
                        <button type="submit" class="w-full mt-3 bg-orange-100 text-orange-700 hover:bg-orange-600 hover:text-white py-2 rounded-lg text-sm font-bold transition-colors">
                            Serahkan Jatah
                        </button>
                    </form>
                    {% else %}
                    <form action="/idul-adha/peta-distribusi/update_status" method="POST">
                        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                        <input type="hidden" name="rt_id" value="{{ rt.id }}">
                        <input type="hidden" name="status" value="Menunggu">
                        <button type="submit" class="w-full mt-3 bg-red-100 text-red-700 hover:bg-red-600 hover:text-white py-2 rounded-lg text-sm font-bold transition-colors">
                            Batal Serahkan
                        </button>
                    </form>
                    {% endif %}
                {% endif %}"""

new_buttons = """                {% if is_admin %}
                    {% if rt.status == 'Menunggu' %}
                    <button onclick="updateRTStatus({{ rt.id }}, 'Diserahkan')" class="w-full mt-3 bg-orange-100 text-orange-700 hover:bg-orange-600 hover:text-white py-2 rounded-lg text-sm font-bold transition-colors">
                        Serahkan Jatah
                    </button>
                    {% else %}
                    <button onclick="updateRTStatus({{ rt.id }}, 'Menunggu')" class="w-full mt-3 bg-red-100 text-red-700 hover:bg-red-600 hover:text-white py-2 rounded-lg text-sm font-bold transition-colors">
                        Batal Serahkan
                    </button>
                    {% endif %}
                {% endif %}"""
content = content.replace(old_buttons, new_buttons)

old_edit_modal = """            <h3 class="text-xl font-bold text-orange-600 mb-4 border-b border-gray-100 pb-2">Edit Data RT</h3>
            <form action="/idul-adha/peta-distribusi/edit" method="POST" class="space-y-4">
                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                <input type="hidden" name="rt_id" id="edit_rt_id">"""

new_edit_modal = """            <h3 class="text-xl font-bold text-orange-600 mb-4 border-b border-gray-100 pb-2">Edit Data RT</h3>
            <form id="editRtForm" class="space-y-4">
                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                <input type="hidden" name="rt_id" id="edit_rt_id">"""
content = content.replace(old_edit_modal, new_edit_modal)


old_edit_btn = """                </div>
                <button type="submit" class="w-full bg-orange-600 text-white font-bold py-2 rounded-xl hover:bg-orange-700 shadow-md mt-2">Save</button>
            </form>
        </div>
    </div>
    <script>
        function openEditRTModal(id, no, rt, ketua, alokasi, status) {
            document.getElementById('edit_rt_id').value = id;
            document.getElementById('edit_nomor_card').value = no;
            document.getElementById('edit_rt_name').value = rt;
            document.getElementById('edit_nama_ketua_rt').value = ketua;
            document.getElementById('edit_alokasi').value = alokasi;
            document.getElementById('edit_status').value = status;
            document.getElementById('modal-edit-rt').classList.remove('hidden');
        }
    </script>
    {% endif %}
</div>
'''"""

new_edit_btn = """                </div>
                <button type="submit" id="editRtBtn" class="w-full bg-orange-600 text-white font-bold py-2 rounded-xl hover:bg-orange-700 shadow-md mt-2 transition-all">Save</button>
            </form>
        </div>
    </div>
    <script>
        function openEditRTModal(id, no, rt, ketua, alokasi, status) {
            document.getElementById('edit_rt_id').value = id;
            document.getElementById('edit_nomor_card').value = no;
            document.getElementById('edit_rt_name').value = rt;
            document.getElementById('edit_nama_ketua_rt').value = ketua;
            document.getElementById('edit_alokasi').value = alokasi;
            document.getElementById('edit_status').value = status;
            document.getElementById('modal-edit-rt').classList.remove('hidden');
        }

        document.addEventListener('DOMContentLoaded', () => {
            const editForm = document.getElementById('editRtForm');
            if(editForm) {
                editForm.addEventListener('submit', async (e) => {
                    e.preventDefault();
                    const btn = document.getElementById('editRtBtn');
                    btn.disabled = true;
                    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Menyimpan...';

                    const formData = new FormData(editForm);
                    const jsonData = Object.fromEntries(formData.entries());
                    const csrfToken = document.querySelector('input[name="csrf_token"]').value;

                    try {
                        const response = await fetch('/idul-adha/peta-distribusi/edit', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                            body: JSON.stringify(jsonData)
                        });
                        const data = await response.json();
                        if(response.ok && data.success) {
                            window.location.reload();
                        } else {
                            alert(data.message || 'Gagal Edit RT');
                            btn.disabled = false;
                            btn.innerHTML = 'Save';
                        }
                    } catch(e) {
                        alert('Kesalahan Jaringan');
                        btn.disabled = false;
                        btn.innerHTML = 'Save';
                    }
                });
            }
        });

        async function updateRTStatus(rtId, newStatus) {
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || document.querySelector('input[name="csrf_token"]')?.value;
            try {
                const response = await fetch('/idul-adha/peta-distribusi/update_status', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                    body: JSON.stringify({ rt_id: rtId, status: newStatus })
                });
                if(response.ok) {
                    window.location.reload();
                }
            } catch(e) {
                console.error("Error updating RT status", e);
            }
        }
    </script>
    {% endif %}
</div>
'''"""
content = content.replace(old_edit_btn, new_edit_btn)

with open("masjid-al-hijrah-65 - alternate - ( idcloudhost - fixing 4 fitur - Idul Adha Qurban - Second Effort).py", "w") as f:
    f.write(content)
