import re

with open("masjid-al-hijrah-65 - alternate - ( idcloudhost - fixing 4 fitur - Idul Adha Qurban - Second Effort).py", "r") as f:
    content = f.read()

# Replace Add RT Form with AJAX
old_add_form = """            <h2 class="text-xl font-bold text-orange-600 mb-4 border-b border-orange-100 pb-2">Tambah Data RT Baru</h2>
            <form action="/idul-adha/peta-distribusi/add" method="POST" class="grid grid-cols-1 md:grid-cols-4 gap-4">
                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">"""

new_add_form = """            <h2 class="text-xl font-bold text-orange-600 mb-4 border-b border-orange-100 pb-2">Tambah Data RT Baru</h2>
            <form id="addRtForm" class="grid grid-cols-1 md:grid-cols-4 gap-4">
                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">"""
content = content.replace(old_add_form, new_add_form)


old_add_btn = """                </div>
                <div class="md:col-span-4 mt-2">
                    <button type="submit" class="w-full bg-orange-600 text-white font-bold py-3 rounded-xl hover:bg-orange-700 shadow-md transition-transform transform hover:-translate-y-1">Tambah Data RT</button>
                </div>
            </form>
        </div>
        {% endif %}"""

new_add_btn = """                </div>
                <div class="md:col-span-4 mt-2">
                    <button type="submit" id="addRtBtn" class="w-full bg-orange-600 text-white font-bold py-3 rounded-xl hover:bg-orange-700 shadow-md transition-all">Tambah Data RT</button>
                </div>
            </form>
        </div>

        <!-- SUCCESS MODAL ANIMATION FOR TAMBAH RT -->
        <div id="generateRTAnim" class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 opacity-0 pointer-events-none transition-opacity duration-300">
            <div class="bg-white rounded-3xl p-8 transform scale-90 transition-transform duration-300 flex flex-col items-center shadow-2xl" id="rtModalContent">
                <div class="w-48 h-32 relative mb-6 overflow-hidden flex items-center justify-center" id="rtCarCont">
                    <div class="absolute bottom-0 w-full h-1 bg-gray-300"></div>
                    <div class="animate-bounce" style="animation: bounce 0.5s infinite alternate;">
                        <i class="fas fa-truck text-6xl text-[#8B2635]"></i>
                    </div>
                    <div class="absolute bottom-0 left-10 flex gap-8">
                        <i class="fas fa-circle-notch text-xl text-gray-800 animate-spin" style="animation: spin 0.5s linear infinite;"></i>
                        <i class="fas fa-circle-notch text-xl text-gray-800 animate-spin" style="animation: spin 0.5s linear infinite;"></i>
                    </div>
                    <div class="absolute bottom-[-2px] w-full flex overflow-hidden">
                        <div class="w-full flex justify-between animate-road" style="animation: roadMove 1s linear infinite;">
                            <div class="w-4 h-1 bg-white"></div><div class="w-4 h-1 bg-white"></div><div class="w-4 h-1 bg-white"></div><div class="w-4 h-1 bg-white"></div><div class="w-4 h-1 bg-white"></div>
                        </div>
                    </div>
                </div>
                <h3 class="text-2xl font-bold text-gray-800 opacity-0 transition-opacity duration-500 delay-300" id="rtText1">Data RT Ditambahkan!</h3>
                <p class="text-gray-500 mt-2 opacity-0 transition-opacity duration-500 delay-500 text-center" id="rtText2">Card status RT telah aktif dan siap dipantau.</p>
            </div>
        </div>

        <style>
        @keyframes roadMove {
            from { transform: translateX(0); }
            to { transform: translateX(-100%); }
        }
        </style>
        {% endif %}"""
content = content.replace(old_add_btn, new_add_btn)

# Prepend AJAX logic to the existing script tag added in patch_peta2
old_script = """        document.addEventListener('DOMContentLoaded', () => {"""
new_script = """        document.addEventListener('DOMContentLoaded', () => {
            const addForm = document.getElementById('addRtForm');
            if(addForm) {
                addForm.addEventListener('submit', async (e) => {
                    e.preventDefault();
                    const btn = document.getElementById('addRtBtn');
                    btn.disabled = true;
                    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Menambah...';

                    const formData = new FormData(addForm);
                    const jsonData = Object.fromEntries(formData.entries());
                    const csrfToken = document.querySelector('input[name="csrf_token"]').value;

                    try {
                        const response = await fetch('/idul-adha/peta-distribusi/add', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                            body: JSON.stringify(jsonData)
                        });

                        const data = await response.json();
                        if(response.ok && data.success) {
                            const modal = document.getElementById('generateRTAnim');
                            const content = document.getElementById('rtModalContent');
                            const text1 = document.getElementById('rtText1');
                            const text2 = document.getElementById('rtText2');

                            modal.classList.remove('opacity-0', 'pointer-events-none');
                            content.classList.remove('scale-90');
                            content.classList.add('scale-100');

                            setTimeout(() => { text1.classList.remove('opacity-0'); text1.classList.add('opacity-100'); }, 1000);
                            setTimeout(() => { text2.classList.remove('opacity-0'); text2.classList.add('opacity-100'); }, 1300);

                            setTimeout(() => {
                                window.location.reload();
                            }, 3000);
                        } else {
                            alert(data.message || 'Gagal menambah RT');
                            btn.disabled = false;
                            btn.innerHTML = 'Tambah Data RT';
                        }
                    } catch(e) {
                        alert('Kesalahan Jaringan');
                        btn.disabled = false;
                        btn.innerHTML = 'Tambah Data RT';
                    }
                });
            }
"""
content = content.replace(old_script, new_script)

with open("masjid-al-hijrah-65 - alternate - ( idcloudhost - fixing 4 fitur - Idul Adha Qurban - Second Effort).py", "w") as f:
    f.write(content)
