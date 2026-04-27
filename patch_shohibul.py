import re

with open("masjid-al-hijrah-65 - alternate - ( idcloudhost - fixing 4 fitur - Idul Adha Qurban - Second Effort).py", "r") as f:
    content = f.read()

# Replace Form Submission with AJAX in IDUL_ADHA_SHOHIBUL_HTML
old_shohibul_html_form = """            <h2 class="text-xl font-bold text-[#8B2635] mb-4">Generate PIN Shohibul</h2>
            <form action="/idul-adha/shohibul/generate" method="POST" class="flex flex-col md:flex-row gap-4">
                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">"""

new_shohibul_html_form = """            <h2 class="text-xl font-bold text-[#8B2635] mb-4">Generate PIN Shohibul</h2>
            <form id="generatePinForm" class="flex flex-col md:flex-row gap-4">
                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">"""

content = content.replace(old_shohibul_html_form, new_shohibul_html_form)


old_shohibul_html_btn = """                </div>
                <div class="md:w-1/4">
                    <label class="block text-sm font-bold text-gray-600 mb-1">&nbsp;</label>
                    <button type="submit" class="w-full bg-[#8B2635] text-white font-bold py-3 rounded-xl hover:bg-red-800 shadow-md">Generate & Save</button>
                </div>
            </form>"""

new_shohibul_html_btn = """                </div>
                <div class="md:w-1/4">
                    <label class="block text-sm font-bold text-gray-600 mb-1">&nbsp;</label>
                    <button type="submit" id="generatePinBtn" class="w-full bg-[#8B2635] text-white font-bold py-3 rounded-xl hover:bg-red-800 shadow-md transition-all">Generate & Save</button>
                </div>
            </form>

            <!-- SUCCESS MODAL ANIMATION FOR PIN GENERATION -->
            <div id="generatePinAnim" class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 opacity-0 pointer-events-none transition-opacity duration-300">
                <div class="bg-white rounded-3xl p-8 transform scale-90 transition-transform duration-300 flex flex-col items-center shadow-2xl" id="pinModalContent">
                    <div class="w-32 h-32 relative flex items-center justify-center mb-6 scale-0 transition-transform duration-500 delay-100" id="pinLogoCont">
                        <!-- Islamic Crescent & Star with filling water effect -->
                        <div class="absolute inset-0 bg-blue-100 rounded-full border-4 border-blue-500 overflow-hidden">
                            <div class="absolute bottom-0 w-full bg-blue-500 rounded-b-full animate-wave h-0" id="waterFill" style="transition: height 1.5s ease-in-out;"></div>
                            <div class="absolute inset-0 flex items-center justify-center z-10 text-white">
                                <i class="fas fa-star-and-crescent text-4xl drop-shadow-md"></i>
                            </div>
                        </div>
                    </div>
                    <h3 class="text-2xl font-bold text-gray-800 opacity-0 transition-opacity duration-500 delay-300" id="pinText1">PIN Shohibul Terbuat!</h3>
                    <p class="text-gray-500 mt-2 opacity-0 transition-opacity duration-500 delay-500 text-center" id="pinText2">Data shohibul telah digenerate, aktif, dan dapat dilacak.</p>
                </div>
            </div>
            """

content = content.replace(old_shohibul_html_btn, new_shohibul_html_btn)


# Update Status buttons to AJAX
old_shohibul_html_status = """                    <form action="/idul-adha/shohibul/update_status" method="POST" class="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                        <input type="hidden" name="pin" value="{{ shohibul.pin }}">
                        <button type="submit" name="status" value="Menunggu Giliran" class="py-3 rounded-xl font-bold border-2 {{ 'border-amber-500 bg-amber-50 text-amber-700' if shohibul.status == 'Menunggu Giliran' else 'border-gray-200 text-gray-500 hover:border-amber-200 hover:text-amber-600' }}">Menunggu</button>
                        <button type="submit" name="status" value="Sedang Disembelih" class="py-3 rounded-xl font-bold border-2 {{ 'border-red-500 bg-red-50 text-red-700' if shohibul.status == 'Sedang Disembelih' else 'border-gray-200 text-gray-500 hover:border-red-200 hover:text-red-600' }}">Disembelih</button>
                        <button type="submit" name="status" value="Proses Pencacahan" class="py-3 rounded-xl font-bold border-2 {{ 'border-blue-500 bg-blue-50 text-blue-700' if shohibul.status == 'Proses Pencacahan' else 'border-gray-200 text-gray-500 hover:border-blue-200 hover:text-blue-600' }}">Pencacahan</button>
                        <button type="submit" name="status" value="Jatah Sohibul Siap Diambil" class="py-3 rounded-xl font-bold border-2 {{ 'border-green-500 bg-green-50 text-green-700' if shohibul.status == 'Jatah Sohibul Siap Diambil' else 'border-gray-200 text-gray-500 hover:border-green-200 hover:text-green-600' }}">Siap Diambil</button>
                    </form>
                </div>
                {% endif %}
            </div>
            {% elif pin %}"""

new_shohibul_html_status = """                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4" id="statusUpdateBtns" data-pin="{{ shohibul.pin }}">
                        <button onclick="updateStatus('Menunggu Giliran', this)" class="status-btn py-3 rounded-xl font-bold border-2 transition-colors {{ 'border-amber-500 bg-amber-50 text-amber-700 active-status' if shohibul.status == 'Menunggu Giliran' else 'border-gray-200 text-gray-500 hover:border-amber-200 hover:text-amber-600' }}">Menunggu</button>
                        <button onclick="updateStatus('Sedang Disembelih', this)" class="status-btn py-3 rounded-xl font-bold border-2 transition-colors {{ 'border-red-500 bg-red-50 text-red-700 active-status' if shohibul.status == 'Sedang Disembelih' else 'border-gray-200 text-gray-500 hover:border-red-200 hover:text-red-600' }}">Disembelih</button>
                        <button onclick="updateStatus('Proses Pencacahan', this)" class="status-btn py-3 rounded-xl font-bold border-2 transition-colors {{ 'border-blue-500 bg-blue-50 text-blue-700 active-status' if shohibul.status == 'Proses Pencacahan' else 'border-gray-200 text-gray-500 hover:border-blue-200 hover:text-blue-600' }}">Pencacahan</button>
                        <button onclick="updateStatus('Jatah Sohibul Siap Diambil', this)" class="status-btn py-3 rounded-xl font-bold border-2 transition-colors {{ 'border-green-500 bg-green-50 text-green-700 active-status' if shohibul.status == 'Jatah Sohibul Siap Diambil' else 'border-gray-200 text-gray-500 hover:border-green-200 hover:text-green-600' }}">Siap Diambil</button>
                    </div>
                </div>
                {% endif %}
            </div>
            {% elif pin %}"""

content = content.replace(old_shohibul_html_status, new_shohibul_html_status)


# Add Shohibul JS & Polling
old_shohibul_html_end = """    </div>
</div>
'''"""

new_shohibul_html_end = """    </div>
</div>
<style>
@keyframes wave {
    0% { transform: translateX(0) scaleY(1); }
    50% { transform: translateX(-25%) scaleY(1.1); }
    100% { transform: translateX(-50%) scaleY(1); }
}
.animate-wave::before {
    content: "";
    position: absolute;
    width: 200%;
    height: 100%;
    background: inherit;
    top: -5px;
    left: 0;
    border-radius: 40% 60% 50% 40% / 40% 50% 60% 40%;
    animation: wave 3s infinite linear;
}
</style>
<script>
document.addEventListener('DOMContentLoaded', () => {
    // 1. PIN Generation AJAX & Animation
    const form = document.getElementById('generatePinForm');
    if(form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = document.getElementById('generatePinBtn');
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generate...';

            const formData = new FormData(form);
            const jsonData = Object.fromEntries(formData.entries());
            const csrfToken = document.querySelector('input[name="csrf_token"]').value;

            try {
                const response = await fetch('/idul-adha/shohibul/generate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify(jsonData)
                });

                const data = await response.json();

                if(response.ok && data.success) {
                    const modal = document.getElementById('generatePinAnim');
                    const content = document.getElementById('pinModalContent');
                    const logoCont = document.getElementById('pinLogoCont');
                    const water = document.getElementById('waterFill');
                    const text1 = document.getElementById('pinText1');
                    const text2 = document.getElementById('pinText2');

                    modal.classList.remove('opacity-0', 'pointer-events-none');
                    content.classList.remove('scale-90');
                    content.classList.add('scale-100');

                    setTimeout(() => { logoCont.classList.remove('scale-0'); logoCont.classList.add('scale-100'); }, 100);
                    setTimeout(() => { water.style.height = '100%'; }, 500);
                    setTimeout(() => { text1.classList.remove('opacity-0'); text1.classList.add('opacity-100'); }, 1500);
                    setTimeout(() => { text2.classList.remove('opacity-0'); text2.classList.add('opacity-100'); }, 1800);

                    setTimeout(() => {
                        window.location.href = '/idul-adha/shohibul?pin=' + data.pin;
                    }, 3500);
                } else {
                    alert(data.message || 'Gagal generate PIN');
                    btn.disabled = false;
                    btn.innerHTML = 'Generate & Save';
                }
            } catch(e) {
                alert('Kesalahan Jaringan');
                btn.disabled = false;
                btn.innerHTML = 'Generate & Save';
            }
        });
    }
});

// 2. Status Update (Admin) AJAX
async function updateStatus(newStatus, btnElement) {
    const btnsCont = document.getElementById('statusUpdateBtns');
    if(!btnsCont) return;
    const pin = btnsCont.dataset.pin;
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || document.querySelector('input[name="csrf_token"]')?.value;

    // Optimistic UI Update for buttons
    const allBtns = btnsCont.querySelectorAll('.status-btn');
    allBtns.forEach(b => {
        b.className = 'status-btn py-3 rounded-xl font-bold border-2 transition-colors border-gray-200 text-gray-500 hover:border-gray-300';
    });

    if(newStatus === 'Menunggu Giliran') btnElement.className = 'status-btn py-3 rounded-xl font-bold border-2 transition-colors border-amber-500 bg-amber-50 text-amber-700 active-status';
    else if(newStatus === 'Sedang Disembelih') btnElement.className = 'status-btn py-3 rounded-xl font-bold border-2 transition-colors border-red-500 bg-red-50 text-red-700 active-status';
    else if(newStatus === 'Proses Pencacahan') btnElement.className = 'status-btn py-3 rounded-xl font-bold border-2 transition-colors border-blue-500 bg-blue-50 text-blue-700 active-status';
    else if(newStatus === 'Jatah Sohibul Siap Diambil') btnElement.className = 'status-btn py-3 rounded-xl font-bold border-2 transition-colors border-green-500 bg-green-50 text-green-700 active-status';

    try {
        const response = await fetch('/idul-adha/shohibul/update_status', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ pin: pin, status: newStatus })
        });
        if(!response.ok) {
            console.error("Failed to update status");
            // Revert optimisitic update on fail could be handled here.
        }
    } catch(e) {
        console.error("Network error updating status", e);
    }
}

// 3. Polling for Live View
{% if shohibul and not is_admin %}
setInterval(async () => {
    try {
        const pin = '{{ shohibul.pin }}';
        const response = await fetch(`/idul-adha/shohibul/status_data?pin=${pin}`);
        if(response.ok) {
            const data = await response.json();
            if(data.success && data.status) {
                // Update Badge dynamically
                const badge = document.getElementById('liveStatusBadge');
                if(badge) {
                    badge.innerHTML = data.status;
                    badge.className = 'px-4 py-2 rounded-full text-sm font-bold ' +
                        (data.status === 'Menunggu Giliran' ? 'bg-amber-100 text-amber-700' :
                         data.status === 'Sedang Disembelih' ? 'bg-red-100 text-red-700' :
                         data.status === 'Proses Pencacahan' ? 'bg-blue-100 text-blue-700' :
                         'bg-green-100 text-green-700 animate-pulse');
                }

                // Update Tracking Bar dynamically
                const steps = ['Menunggu Giliran', 'Sedang Disembelih', 'Proses Pencacahan', 'Jatah Sohibul Siap Diambil'];
                const currentIndex = steps.indexOf(data.status);

                ['step-1', 'step-2', 'step-3', 'step-4'].forEach((id, idx) => {
                    const el = document.getElementById(id);
                    if(!el) return;
                    if(idx < currentIndex) {
                        el.className = 'w-10 h-10 md:w-14 md:h-14 rounded-full flex items-center justify-center font-bold relative z-10 transition-colors duration-500 bg-green-500 text-white';
                        el.innerHTML = '<i class="fas fa-check"></i>';
                    } else if(idx === currentIndex) {
                        el.className = 'w-10 h-10 md:w-14 md:h-14 rounded-full flex items-center justify-center font-bold relative z-10 transition-colors duration-500 bg-[#8B2635] text-white ring-4 ring-red-100';
                        el.innerHTML = (idx+1).toString();
                    } else {
                        el.className = 'w-10 h-10 md:w-14 md:h-14 rounded-full flex items-center justify-center font-bold relative z-10 transition-colors duration-500 bg-gray-200 text-gray-400';
                        el.innerHTML = (idx+1).toString();
                    }
                });

                const line = document.getElementById('progressLine');
                if(line) {
                    if(currentIndex === 0) line.className = 'h-full bg-[#8B2635] transition-all duration-1000 w-[0%]';
                    else if(currentIndex === 1) line.className = 'h-full bg-[#8B2635] transition-all duration-1000 w-[33%]';
                    else if(currentIndex === 2) line.className = 'h-full bg-[#8B2635] transition-all duration-1000 w-[66%]';
                    else if(currentIndex === 3) line.className = 'h-full bg-[#8B2635] transition-all duration-1000 w-[100%]';
                }
            }
        }
    } catch(e) {
        console.error("Polling error", e);
    }
}, 3000); // Poll every 3 seconds
{% endif %}
</script>
'''"""

content = content.replace(old_shohibul_html_end, new_shohibul_html_end)

# Add IDs to the tracking steps in IDUL_ADHA_SHOHIBUL_HTML for dynamic updates
tracking_old = """                    <div class="flex justify-between relative">
                        <div class="absolute top-1/2 left-0 w-full h-1 bg-gray-200 -translate-y-1/2 z-0"></div>
                        <div class="absolute top-1/2 left-0 h-1 bg-[#8B2635] -translate-y-1/2 z-0 transition-all duration-1000" style="width: {{ '0%' if shohibul.status == 'Menunggu Giliran' else '33%' if shohibul.status == 'Sedang Disembelih' else '66%' if shohibul.status == 'Proses Pencacahan' else '100%' }}"></div>

                        <!-- Step 1 -->
                        <div class="w-10 h-10 md:w-14 md:h-14 rounded-full flex items-center justify-center font-bold relative z-10 transition-colors duration-500 {{ 'bg-green-500 text-white' if shohibul.status in ['Sedang Disembelih', 'Proses Pencacahan', 'Jatah Sohibul Siap Diambil'] else 'bg-[#8B2635] text-white ring-4 ring-red-100' }}">
                            {% if shohibul.status in ['Sedang Disembelih', 'Proses Pencacahan', 'Jatah Sohibul Siap Diambil'] %}<i class="fas fa-check"></i>{% else %}1{% endif %}
                        </div>

                        <!-- Step 2 -->
                        <div class="w-10 h-10 md:w-14 md:h-14 rounded-full flex items-center justify-center font-bold relative z-10 transition-colors duration-500 {{ 'bg-green-500 text-white' if shohibul.status in ['Proses Pencacahan', 'Jatah Sohibul Siap Diambil'] else 'bg-[#8B2635] text-white ring-4 ring-red-100' if shohibul.status == 'Sedang Disembelih' else 'bg-gray-200 text-gray-400' }}">
                            {% if shohibul.status in ['Proses Pencacahan', 'Jatah Sohibul Siap Diambil'] %}<i class="fas fa-check"></i>{% else %}2{% endif %}
                        </div>

                        <!-- Step 3 -->
                        <div class="w-10 h-10 md:w-14 md:h-14 rounded-full flex items-center justify-center font-bold relative z-10 transition-colors duration-500 {{ 'bg-green-500 text-white' if shohibul.status == 'Jatah Sohibul Siap Diambil' else 'bg-[#8B2635] text-white ring-4 ring-red-100' if shohibul.status == 'Proses Pencacahan' else 'bg-gray-200 text-gray-400' }}">
                            {% if shohibul.status == 'Jatah Sohibul Siap Diambil' %}<i class="fas fa-check"></i>{% else %}3{% endif %}
                        </div>

                        <!-- Step 4 -->
                        <div class="w-10 h-10 md:w-14 md:h-14 rounded-full flex items-center justify-center font-bold relative z-10 transition-colors duration-500 {{ 'bg-[#8B2635] text-white ring-4 ring-red-100' if shohibul.status == 'Jatah Sohibul Siap Diambil' else 'bg-gray-200 text-gray-400' }}">
                            4
                        </div>
                    </div>"""

tracking_new = """                    <div class="flex justify-between relative">
                        <div class="absolute top-1/2 left-0 w-full h-1 bg-gray-200 -translate-y-1/2 z-0"></div>
                        <div id="progressLine" class="absolute top-1/2 left-0 h-1 bg-[#8B2635] -translate-y-1/2 z-0 transition-all duration-1000" style="width: {{ '0%' if shohibul.status == 'Menunggu Giliran' else '33%' if shohibul.status == 'Sedang Disembelih' else '66%' if shohibul.status == 'Proses Pencacahan' else '100%' }}"></div>

                        <!-- Step 1 -->
                        <div id="step-1" class="w-10 h-10 md:w-14 md:h-14 rounded-full flex items-center justify-center font-bold relative z-10 transition-colors duration-500 {{ 'bg-green-500 text-white' if shohibul.status in ['Sedang Disembelih', 'Proses Pencacahan', 'Jatah Sohibul Siap Diambil'] else 'bg-[#8B2635] text-white ring-4 ring-red-100' }}">
                            {% if shohibul.status in ['Sedang Disembelih', 'Proses Pencacahan', 'Jatah Sohibul Siap Diambil'] %}<i class="fas fa-check"></i>{% else %}1{% endif %}
                        </div>

                        <!-- Step 2 -->
                        <div id="step-2" class="w-10 h-10 md:w-14 md:h-14 rounded-full flex items-center justify-center font-bold relative z-10 transition-colors duration-500 {{ 'bg-green-500 text-white' if shohibul.status in ['Proses Pencacahan', 'Jatah Sohibul Siap Diambil'] else 'bg-[#8B2635] text-white ring-4 ring-red-100' if shohibul.status == 'Sedang Disembelih' else 'bg-gray-200 text-gray-400' }}">
                            {% if shohibul.status in ['Proses Pencacahan', 'Jatah Sohibul Siap Diambil'] %}<i class="fas fa-check"></i>{% else %}2{% endif %}
                        </div>

                        <!-- Step 3 -->
                        <div id="step-3" class="w-10 h-10 md:w-14 md:h-14 rounded-full flex items-center justify-center font-bold relative z-10 transition-colors duration-500 {{ 'bg-green-500 text-white' if shohibul.status == 'Jatah Sohibul Siap Diambil' else 'bg-[#8B2635] text-white ring-4 ring-red-100' if shohibul.status == 'Proses Pencacahan' else 'bg-gray-200 text-gray-400' }}">
                            {% if shohibul.status == 'Jatah Sohibul Siap Diambil' %}<i class="fas fa-check"></i>{% else %}3{% endif %}
                        </div>

                        <!-- Step 4 -->
                        <div id="step-4" class="w-10 h-10 md:w-14 md:h-14 rounded-full flex items-center justify-center font-bold relative z-10 transition-colors duration-500 {{ 'bg-[#8B2635] text-white ring-4 ring-red-100' if shohibul.status == 'Jatah Sohibul Siap Diambil' else 'bg-gray-200 text-gray-400' }}">
                            4
                        </div>
                    </div>"""

content = content.replace(tracking_old, tracking_new)

# Add id to live status badge
badge_old = """                            <span class="px-4 py-2 rounded-full text-sm font-bold {{ 'bg-amber-100 text-amber-700' if shohibul.status == 'Menunggu Giliran' else 'bg-red-100 text-red-700' if shohibul.status == 'Sedang Disembelih' else 'bg-blue-100 text-blue-700' if shohibul.status == 'Proses Pencacahan' else 'bg-green-100 text-green-700 animate-pulse' }}">{{ shohibul.status }}</span>"""
badge_new = """                            <span id="liveStatusBadge" class="px-4 py-2 rounded-full text-sm font-bold {{ 'bg-amber-100 text-amber-700' if shohibul.status == 'Menunggu Giliran' else 'bg-red-100 text-red-700' if shohibul.status == 'Sedang Disembelih' else 'bg-blue-100 text-blue-700' if shohibul.status == 'Proses Pencacahan' else 'bg-green-100 text-green-700 animate-pulse' }}">{{ shohibul.status }}</span>"""
content = content.replace(badge_old, badge_new)


# Update Backend Route idul_adha_shohibul_generate
old_shohibul_gen_route = """@app.route('/idul-adha/shohibul/generate', methods=['POST'])
def idul_adha_shohibul_generate():
    if not session.get('is_admin'): return redirect(url_for('idul_adha_shohibul'))
    jenis = request.form.get('jenis_hewan')
    nama = request.form.get('nama_shohibul')
    prefix = 'SQ' if jenis == 'Sapi' else 'KQ'
    last_record = QurbanShohibul.query.filter(QurbanShohibul.pin.like(f"{prefix}-%")).order_by(QurbanShohibul.id.desc()).first()
    if last_record:
        last_num = int(last_record.pin.split('-')[1])
        next_num = last_num + 1
    else:
        next_num = 1
    new_pin = f"{prefix}-{next_num:03d}"
    shohibul = QurbanShohibul(pin=new_pin, jenis_hewan=jenis, nama_shohibul=nama)
    try:
        db.session.add(shohibul)
        db.session.commit()
        flash(f"Berhasil meng-generate PIN {new_pin}", "success")
    except Exception as e:
        db.session.rollback()
        flash("Gagal meng-generate PIN", "error")
        app.logger.error(f"Error in idul_adha_shohibul_generate: {e}", exc_info=True)
    return redirect(url_for('idul_adha_shohibul', pin=new_pin))"""

new_shohibul_gen_route = """@app.route('/idul-adha/shohibul/generate', methods=['POST'])
def idul_adha_shohibul_generate():
    if not session.get('is_admin'): return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    try:
        req_data = request.get_json(silent=True) or request.form
        jenis = req_data.get('jenis_hewan')
        nama = req_data.get('nama_shohibul')
        prefix = 'SQ' if jenis == 'Sapi' else 'KQ'
        last_record = QurbanShohibul.query.filter(QurbanShohibul.pin.like(f"{prefix}-%")).order_by(QurbanShohibul.id.desc()).first()
        if last_record:
            last_num = int(last_record.pin.split('-')[1])
            next_num = last_num + 1
        else:
            next_num = 1
        new_pin = f"{prefix}-{next_num:03d}"
        shohibul = QurbanShohibul(pin=new_pin, jenis_hewan=jenis, nama_shohibul=nama)
        db.session.add(shohibul)
        db.session.commit()
        if request.is_json:
            return jsonify({'success': True, 'pin': new_pin, 'message': f'Berhasil meng-generate PIN {new_pin}'})
        else:
            flash(f"Berhasil meng-generate PIN {new_pin}", "success")
            return redirect(url_for('idul_adha_shohibul', pin=new_pin))
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in idul_adha_shohibul_generate: {e}", exc_info=True)
        if request.is_json:
            return jsonify({'success': False, 'message': 'Gagal meng-generate PIN'})
        else:
            flash("Gagal meng-generate PIN", "error")
            return redirect(url_for('idul_adha_shohibul'))"""

content = content.replace(old_shohibul_gen_route, new_shohibul_gen_route)

# Update Backend Route idul_adha_shohibul_update_status
old_shohibul_upd_route = """@app.route('/idul-adha/shohibul/update_status', methods=['POST'])
def idul_adha_shohibul_update_status():
    if not session.get('is_admin'): return redirect(url_for('idul_adha_shohibul'))
    pin = request.form.get('pin')
    status = request.form.get('status')
    shohibul = QurbanShohibul.query.filter_by(pin=pin).first()
    if shohibul:
        shohibul.status = status
        try:
            db.session.commit()
            flash(f"Status PIN {pin} berhasil diupdate.", "success")
        except Exception as e:
            db.session.rollback()
            flash("Gagal mengupdate status.", "error")
            app.logger.error(f"Error in idul_adha_shohibul_update_status: {e}", exc_info=True)
    return redirect(url_for('idul_adha_shohibul', pin=pin))"""

new_shohibul_upd_route = """@app.route('/idul-adha/shohibul/update_status', methods=['POST'])
@csrf.exempt
def idul_adha_shohibul_update_status():
    if not session.get('is_admin'): return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    try:
        req_data = request.get_json(silent=True) or request.form
        pin = req_data.get('pin')
        status = req_data.get('status')
        shohibul = QurbanShohibul.query.filter_by(pin=pin).first()
        if shohibul:
            shohibul.status = status
            db.session.commit()
            if request.is_json:
                return jsonify({'success': True, 'message': f'Status PIN {pin} berhasil diupdate.'})
            else:
                flash(f"Status PIN {pin} berhasil diupdate.", "success")
                return redirect(url_for('idul_adha_shohibul', pin=pin))
        return jsonify({'success': False, 'message': 'Not found'}), 404
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in idul_adha_shohibul_update_status: {e}", exc_info=True)
        if request.is_json:
            return jsonify({'success': False, 'message': 'Gagal mengupdate status.'}), 500
        return redirect(url_for('idul_adha_shohibul', pin=pin))

@app.route('/idul-adha/shohibul/status_data', methods=['GET'])
def idul_adha_shohibul_status_data():
    pin = request.args.get('pin')
    if not pin: return jsonify({'success': False, 'message': 'No PIN'}), 400
    shohibul = QurbanShohibul.query.filter_by(pin=pin).first()
    if shohibul:
        return jsonify({'success': True, 'status': shohibul.status})
    return jsonify({'success': False, 'message': 'Not found'}), 404"""

content = content.replace(old_shohibul_upd_route, new_shohibul_upd_route)

with open("masjid-al-hijrah-65 - alternate - ( idcloudhost - fixing 4 fitur - Idul Adha Qurban - Second Effort).py", "w") as f:
    f.write(content)
