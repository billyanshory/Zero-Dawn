import re

with open("masjid-al-hijrah-64 ( idcloudhost - fixing 4 fitur - Idul Adha Qurban ).py", "r") as f:
    content = f.read()

# Add public route for Peta Distribusi if it doesn't exist
peta_route = """@app.route('/idul-adha/peta', methods=['GET'])
def public_qurban_peta():
    try:
        slots = DistribusiSlot.query.order_by(DistribusiSlot.time_start.asc()).all()

        total_rt = len(slots)
        total_quota = sum(s.total_quota for s in slots)
        total_distributed = sum(s.distributed_count for s in slots)

        missing_rts = [s.rt_identifier for s in slots if not s.is_locked]

        rendered_content = render_template_string(IDUL_ADHA_PETA_DISTRIBUSI_HTML,
                                                  slots=slots,
                                                  total_rt=total_rt,
                                                  total_quota=total_quota,
                                                  total_distributed=total_distributed,
                                                  missing_rts=missing_rts,
                                                  is_admin=session.get('is_admin', False),
                                                  settings=get_settings())
        return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, active_page='idul-adha', content=rendered_content, is_admin=session.get('is_admin', False), settings=get_settings())

    except Exception as e:
        app.logger.error(f"Error in public peta distribusi: {e}")
        return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, active_page='idul-adha', content="<div class='min-h-screen flex items-center justify-center p-4'><div class='bg-white p-8 rounded-3xl shadow-xl max-w-md text-center'><i class='fas fa-exclamation-triangle text-4xl text-amber-500 mb-4'></i><h3 class='text-xl font-bold text-gray-800 mb-2'>Sedang Menyiapkan Peta</h3><p class='text-gray-600 mb-4'>Data peta distribusi belum tersedia atau sedang dalam pembaruan.</p><a href='/idul-adha' class='inline-block bg-[#1B4332] text-white px-6 py-2 rounded-xl font-bold'>Kembali</a></div></div>", is_admin=session.get('is_admin', False), settings=get_settings())

"""

if 'def public_qurban_peta():' not in content:
    content = content.replace(
        "@app.route('/admin/qurban/peta', methods=['GET', 'POST'])",
        peta_route + "@app.route('/admin/qurban/peta', methods=['GET', 'POST'])"
    )

with open("masjid-al-hijrah-64 ( idcloudhost - fixing 4 fitur - Idul Adha Qurban ).py", "w") as f:
    f.write(content)
