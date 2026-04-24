import re

with open("masjid-al-hijrah-63 ( idcloudhost - others 5 fitur - Idul Adha Qurban ).py", "r") as f:
    content = f.read()

route_update = """@app.route('/admin/qurban/peta')
def admin_qurban_peta():
    if not session.get('is_admin'):
        return redirect(url_for('index'))

    try:
        slots = DistribusiSlot.query.all()
        total_rt = len(slots)
        total_quota = sum([s.total_quota for s in slots])
        total_distributed = sum([s.distributed_count for s in slots])
        missing_rts = [s.rt_identifier for s in slots if not s.is_locked]

        rendered_content = render_template_string(IDUL_ADHA_PETA_DISTRIBUSI_HTML,
                                                  slots=slots,
                                                  total_rt=total_rt,
                                                  total_quota=total_quota,
                                                  total_distributed=total_distributed,
                                                  missing_rts=missing_rts,
                                                  is_admin=True,
                                                  settings=get_settings())
        return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, active_page='idul-adha', content=rendered_content, is_admin=True, settings=get_settings())
    except Exception as e:
        app.logger.error(f"Error loading Peta Distribusi: {e}", exc_info=True)
        return "Internal Server Error", 500"""

content = re.sub(r"@app\.route\('/admin/qurban/peta'.*?return \"Internal Server Error\", 500\).*?return \"Internal Server Error\", 500", route_update.strip(), content, flags=re.DOTALL)

with open("masjid-al-hijrah-63 ( idcloudhost - others 5 fitur - Idul Adha Qurban ).py", "w") as f:
    f.write(content)
