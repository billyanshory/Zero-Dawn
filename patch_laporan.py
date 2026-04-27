import re

with open("masjid-al-hijrah-65 - alternate - ( idcloudhost - fixing 4 fitur - Idul Adha Qurban - Second Effort).py", "r") as f:
    content = f.read()

# Replace Form Submission with AJAX and add Modal HTML/CSS in IDUL_ADHA_LAPORAN_HTML
old_laporan_html = """            <h2 class="text-xl font-bold text-[#8B2635] mb-4">Edit Data Laporan Qurban</h2>
            <form action="/idul-adha/laporan" method="POST" class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">"""

new_laporan_html = """            <h2 class="text-xl font-bold text-[#8B2635] mb-4">Edit Data Laporan Qurban</h2>
            <form id="laporanForm" class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">"""

content = content.replace(old_laporan_html, new_laporan_html)

old_laporan_html2 = """                <div class="md:col-span-2 mt-2">
                    <button type="submit" class="w-full bg-[#8B2635] text-white font-bold py-3 rounded-xl hover:bg-red-800 shadow-md">Save / Update Data</button>
                </div>
            </form>
        </div>
        {% endif %}"""

new_laporan_html2 = """                <div class="md:col-span-2 mt-2">
                    <button type="submit" id="submitLaporanBtn" class="w-full bg-[#8B2635] text-white font-bold py-3 rounded-xl hover:bg-red-800 shadow-md transition-all">Save / Update Data</button>
                </div>
            </form>
        </div>

        <!-- SUCCESS MODAL ANIMATION -->
        <div id="laporanSuccessAnim" class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 opacity-0 pointer-events-none transition-opacity duration-300">
            <div class="bg-white rounded-3xl p-8 transform scale-90 transition-transform duration-300 flex flex-col items-center shadow-2xl" id="laporanModalContent">
                <div class="w-24 h-24 rounded-full bg-green-100 flex items-center justify-center mb-4 border-4 border-green-500 scale-0 transition-transform duration-500 delay-100" id="laporanCheck">
                    <i class="fas fa-check text-5xl text-green-500"></i>
                </div>
                <h3 class="text-2xl font-bold text-gray-800 opacity-0 transition-opacity duration-500 delay-300" id="laporanText1">Berhasil Disimpan</h3>
                <p class="text-gray-500 mt-2 opacity-0 transition-opacity duration-500 delay-500" id="laporanText2">Data laporan qurban telah diupdate secara realtime.</p>
            </div>
        </div>

        <script>
        document.addEventListener('DOMContentLoaded', () => {
            const form = document.getElementById('laporanForm');
            if(form) {
                form.addEventListener('submit', async (e) => {
                    e.preventDefault();
                    const btn = document.getElementById('submitLaporanBtn');
                    btn.disabled = true;
                    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Menyimpan...';

                    const formData = new FormData(form);
                    const jsonData = Object.fromEntries(formData.entries());
                    const csrfToken = document.querySelector('input[name="csrf_token"]').value;

                    try {
                        const response = await fetch('/idul-adha/laporan', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRFToken': csrfToken
                            },
                            body: JSON.stringify(jsonData)
                        });

                        const data = await response.json();

                        if(response.ok && data.success) {
                            // Play Animation
                            const modal = document.getElementById('laporanSuccessAnim');
                            const content = document.getElementById('laporanModalContent');
                            const check = document.getElementById('laporanCheck');
                            const text1 = document.getElementById('laporanText1');
                            const text2 = document.getElementById('laporanText2');

                            modal.classList.remove('opacity-0', 'pointer-events-none');
                            content.classList.remove('scale-90');
                            content.classList.add('scale-100');

                            setTimeout(() => { check.classList.remove('scale-0'); check.classList.add('scale-100'); }, 100);
                            setTimeout(() => { text1.classList.remove('opacity-0'); text1.classList.add('opacity-100'); }, 300);
                            setTimeout(() => { text2.classList.remove('opacity-0'); text2.classList.add('opacity-100'); }, 500);

                            setTimeout(() => {
                                window.location.reload();
                            }, 2500);
                        } else {
                            alert(data.message || 'Terjadi kesalahan');
                            btn.disabled = false;
                            btn.innerHTML = 'Save / Update Data';
                        }
                    } catch (error) {
                        alert('Terjadi kesalahan jaringan');
                        btn.disabled = false;
                        btn.innerHTML = 'Save / Update Data';
                    }
                });
            }
        });
        </script>
        {% endif %}"""

content = content.replace(old_laporan_html2, new_laporan_html2)

# Update Backend Route idul_adha_laporan
old_laporan_route = """    if request.method == 'POST' and session.get('is_admin'):
        report.total_sapi = int(request.form.get('total_sapi', 0))
        report.total_kambing = int(request.form.get('total_kambing', 0))
        report.estimasi_daging = int(request.form.get('estimasi_daging', 0))
        report.paket_terdistribusi = int(request.form.get('paket_terdistribusi', 0))
        report.paket_total = int(request.form.get('paket_total', 0))
        try:
            db.session.commit()
            flash("Data berhasil disimpan", "success")
        except Exception as e:
            db.session.rollback()
            flash("Gagal menyimpan data karena kesalahan server", "error")
            app.logger.error(f"Error updating QurbanReport: {e}", exc_info=True)
        return redirect(url_for('idul_adha_laporan'))"""

new_laporan_route = """    if request.method == 'POST' and session.get('is_admin'):
        try:
            req_data = request.get_json(silent=True) or request.form
            report.total_sapi = int(req_data.get('total_sapi', 0))
            report.total_kambing = int(req_data.get('total_kambing', 0))
            report.estimasi_daging = int(req_data.get('estimasi_daging', 0))
            report.paket_terdistribusi = int(req_data.get('paket_terdistribusi', 0))
            report.paket_total = int(req_data.get('paket_total', 0))
            db.session.commit()

            if request.is_json:
                return jsonify({'success': True, 'message': 'Data berhasil disimpan'})
            else:
                flash("Data berhasil disimpan", "success")
                return redirect(url_for('idul_adha_laporan'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error updating QurbanReport: {e}", exc_info=True)
            if request.is_json:
                return jsonify({'success': False, 'message': 'Kesalahan server'}), 500
            else:
                flash("Gagal menyimpan data karena kesalahan server", "error")
                return redirect(url_for('idul_adha_laporan'))"""

content = content.replace(old_laporan_route, new_laporan_route)

with open("masjid-al-hijrah-65 - alternate - ( idcloudhost - fixing 4 fitur - Idul Adha Qurban - Second Effort).py", "w") as f:
    f.write(content)
