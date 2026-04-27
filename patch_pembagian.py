import re

with open("masjid-al-hijrah-65 - alternate - ( idcloudhost - fixing 4 fitur - Idul Adha Qurban - Second Effort).py", "r") as f:
    content = f.read()

# Replace Form Submission with AJAX in IDUL_ADHA_PEMBAGIAN_HTML
old_pembagian_html_form = """            <h2 class="text-xl font-bold text-[#8B2635] mb-4">Generate E-Kupon Qurban</h2>
            <form action="/idul-adha/pembagian/generate" method="POST" class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">"""

new_pembagian_html_form = """            <h2 class="text-xl font-bold text-[#8B2635] mb-4">Generate E-Kupon Qurban</h2>
            <form id="generateKuponForm" class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">"""

content = content.replace(old_pembagian_html_form, new_pembagian_html_form)


old_pembagian_html_btn = """                <div class="md:col-span-2 mt-2">
                    <button type="submit" class="w-full bg-[#8B2635] text-white font-bold py-3 rounded-xl hover:bg-red-800 shadow-md">Generate & Save Kupon</button>
                </div>
            </form>
        </div>
        {% endif %}"""

new_pembagian_html_btn = """                <div class="md:col-span-2 mt-2">
                    <button type="submit" id="generateKuponBtn" class="w-full bg-[#8B2635] text-white font-bold py-3 rounded-xl hover:bg-red-800 shadow-md transition-all">Generate & Save Kupon</button>
                </div>
            </form>
        </div>

        <!-- SUCCESS MODAL ANIMATION FOR KUPON GENERATION -->
        <div id="generateKuponAnim" class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 opacity-0 pointer-events-none transition-opacity duration-300">
            <div class="bg-white rounded-3xl p-8 transform scale-90 transition-transform duration-300 flex flex-col items-center shadow-2xl" id="kuponModalContent">
                <div class="w-32 h-32 relative mb-6 scale-0 transition-transform duration-500 delay-100" id="kuponSketchCont">
                    <svg viewBox="0 0 100 100" class="w-full h-full text-[#8B2635]">
                        <path id="cowPath" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"
                              d="M20,60 C20,40 30,30 50,30 C70,30 80,40 80,60 C80,80 70,80 50,80 C30,80 20,80 20,60 Z M30,35 L20,20 M70,35 L80,20"
                              style="stroke-dasharray: 200; stroke-dashoffset: 200;" />
                    </svg>
                </div>
                <h3 class="text-2xl font-bold text-gray-800 opacity-0 transition-opacity duration-500 delay-300" id="kuponText1">E-Kupon Dibuat!</h3>
                <p class="text-gray-500 mt-2 opacity-0 transition-opacity duration-500 delay-500 text-center" id="kuponText2">E-Kupon Qurban Warga telah aktif dan siap dilacak.</p>
            </div>
        </div>

        <style>
        @keyframes drawCow {
            to { stroke-dashoffset: 0; }
        }
        .animate-draw {
            animation: drawCow 1.5s ease-in-out forwards;
        }
        </style>
        <script>
        document.addEventListener('DOMContentLoaded', () => {
            const form = document.getElementById('generateKuponForm');
            if(form) {
                form.addEventListener('submit', async (e) => {
                    e.preventDefault();
                    const btn = document.getElementById('generateKuponBtn');
                    btn.disabled = true;
                    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generate...';

                    const formData = new FormData(form);
                    const jsonData = Object.fromEntries(formData.entries());
                    const csrfToken = document.querySelector('input[name="csrf_token"]').value;

                    try {
                        const response = await fetch('/idul-adha/pembagian/generate', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRFToken': csrfToken
                            },
                            body: JSON.stringify(jsonData)
                        });

                        const data = await response.json();

                        if(response.ok && data.success) {
                            const modal = document.getElementById('generateKuponAnim');
                            const content = document.getElementById('kuponModalContent');
                            const sketchCont = document.getElementById('kuponSketchCont');
                            const cowPath = document.getElementById('cowPath');
                            const text1 = document.getElementById('kuponText1');
                            const text2 = document.getElementById('kuponText2');

                            modal.classList.remove('opacity-0', 'pointer-events-none');
                            content.classList.remove('scale-90');
                            content.classList.add('scale-100');

                            setTimeout(() => {
                                sketchCont.classList.remove('scale-0');
                                sketchCont.classList.add('scale-100');
                                cowPath.classList.add('animate-draw');
                            }, 100);
                            setTimeout(() => { text1.classList.remove('opacity-0'); text1.classList.add('opacity-100'); }, 1500);
                            setTimeout(() => { text2.classList.remove('opacity-0'); text2.classList.add('opacity-100'); }, 1800);

                            setTimeout(() => {
                                window.location.href = '/idul-adha/distribution?q=' + data.kupon;
                            }, 3500);
                        } else {
                            alert(data.message || 'Gagal generate Kupon');
                            btn.disabled = false;
                            btn.innerHTML = 'Generate & Save Kupon';
                        }
                    } catch(e) {
                        alert('Kesalahan Jaringan');
                        btn.disabled = false;
                        btn.innerHTML = 'Generate & Save Kupon';
                    }
                });
            }
        });
        </script>
        {% endif %}"""

content = content.replace(old_pembagian_html_btn, new_pembagian_html_btn)


# Update Backend Route idul_adha_pembagian_generate
old_pembagian_gen_route = """@app.route('/idul-adha/pembagian/generate', methods=['POST'])
def idul_adha_pembagian_generate():
    if not session.get('is_admin'): return redirect(url_for('idul_adha_distribution'))
    nama = request.form.get('nama_penerima')
    rt = request.form.get('rt')
    waktu = request.form.get('waktu_pengambilan')
    lokasi = request.form.get('lokasi_pengambilan')
    last_record = QurbanKupon.query.filter(QurbanKupon.nomor_kupon.like("KPN-%")).order_by(QurbanKupon.id.desc()).first()
    if last_record:
        last_num = int(last_record.nomor_kupon.split('-')[1])
        next_num = last_num + 1
    else:
        next_num = 1
    new_kupon = f"KPN-{next_num:03d}"
    kupon_entry = QurbanKupon(nomor_kupon=new_kupon, nama_penerima=nama, rt=rt, waktu_pengambilan=waktu, lokasi_pengambilan=lokasi)
    try:
        db.session.add(kupon_entry)
        db.session.commit()
        flash(f"Berhasil meng-generate Kupon {new_kupon}", "success")
    except Exception as e:
        db.session.rollback()
        flash("Gagal meng-generate Kupon", "error")
        app.logger.error(f"Error in idul_adha_pembagian_generate: {e}", exc_info=True)
    return redirect(url_for('idul_adha_distribution', q=new_kupon))"""

new_pembagian_gen_route = """@app.route('/idul-adha/pembagian/generate', methods=['POST'])
def idul_adha_pembagian_generate():
    if not session.get('is_admin'): return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    try:
        req_data = request.get_json(silent=True) or request.form
        nama = req_data.get('nama_penerima')
        rt = req_data.get('rt')
        waktu = req_data.get('waktu_pengambilan')
        lokasi = req_data.get('lokasi_pengambilan')
        last_record = QurbanKupon.query.filter(QurbanKupon.nomor_kupon.like("KPN-%")).order_by(QurbanKupon.id.desc()).first()
        if last_record:
            last_num = int(last_record.nomor_kupon.split('-')[1])
            next_num = last_num + 1
        else:
            next_num = 1
        new_kupon = f"KPN-{next_num:03d}"
        kupon_entry = QurbanKupon(nomor_kupon=new_kupon, nama_penerima=nama, rt=rt, waktu_pengambilan=waktu, lokasi_pengambilan=lokasi)
        db.session.add(kupon_entry)
        db.session.commit()
        if request.is_json:
            return jsonify({'success': True, 'kupon': new_kupon, 'message': f'Berhasil meng-generate Kupon {new_kupon}'})
        else:
            flash(f"Berhasil meng-generate Kupon {new_kupon}", "success")
            return redirect(url_for('idul_adha_distribution', q=new_kupon))
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in idul_adha_pembagian_generate: {e}", exc_info=True)
        if request.is_json:
            return jsonify({'success': False, 'message': 'Gagal meng-generate Kupon'}), 500
        else:
            flash("Gagal meng-generate Kupon", "error")
            return redirect(url_for('idul_adha_distribution'))"""

content = content.replace(old_pembagian_gen_route, new_pembagian_gen_route)

with open("masjid-al-hijrah-65 - alternate - ( idcloudhost - fixing 4 fitur - Idul Adha Qurban - Second Effort).py", "w") as f:
    f.write(content)
