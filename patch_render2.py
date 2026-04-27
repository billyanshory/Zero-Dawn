import re

with open("masjid-al-hijrah-63 - alternate - ( idcloudhost - others 5 fitur - Idul Adha Qurban ).py", "r") as f:
    content = f.read()

# Manual patch since regex didn't catch it correctly due to newlines/spacing

# 1. Laporan
laporan_old = """    return render_template_string(BASE_LAYOUT,
                                  styles=STYLES_HTML,
                                  active_page='idul-adha',
                                  content=IDUL_ADHA_LAPORAN_HTML,
                                  report=report,
                                  is_admin=session.get('is_admin', False),
                                  settings=get_settings())"""
laporan_new = """    rendered_content = render_template_string(IDUL_ADHA_LAPORAN_HTML,
                                              report=report,
                                              is_admin=session.get('is_admin', False),
                                              settings=get_settings())
    return render_template_string(BASE_LAYOUT,
                                  styles=STYLES_HTML,
                                  active_page='idul-adha',
                                  content=rendered_content,
                                  is_admin=session.get('is_admin', False),
                                  settings=get_settings())"""
content = content.replace(laporan_old, laporan_new)

# 2. Shohibul
shohibul_old = """    return render_template_string(BASE_LAYOUT,
                                  styles=STYLES_HTML,
                                  active_page='idul-adha',
                                  content=IDUL_ADHA_SHOHIBUL_HTML,
                                  shohibul=shohibul,
                                  is_admin=session.get('is_admin', False),
                                  settings=get_settings())"""
shohibul_new = """    rendered_content = render_template_string(IDUL_ADHA_SHOHIBUL_HTML,
                                              shohibul=shohibul,
                                              is_admin=session.get('is_admin', False),
                                              settings=get_settings())
    return render_template_string(BASE_LAYOUT,
                                  styles=STYLES_HTML,
                                  active_page='idul-adha',
                                  content=rendered_content,
                                  is_admin=session.get('is_admin', False),
                                  settings=get_settings())"""
content = content.replace(shohibul_old, shohibul_new)

# 3. Pembagian
pembagian_old = """    return render_template_string(BASE_LAYOUT,
                                  styles=STYLES_HTML,
                                  active_page='idul-adha',
                                  content=IDUL_ADHA_PEMBAGIAN_HTML,
                                  kupon=kupon,
                                  is_admin=session.get('is_admin', False),
                                  settings=get_settings())"""
pembagian_new = """    rendered_content = render_template_string(IDUL_ADHA_PEMBAGIAN_HTML,
                                              kupon=kupon,
                                              is_admin=session.get('is_admin', False),
                                              settings=get_settings())
    return render_template_string(BASE_LAYOUT,
                                  styles=STYLES_HTML,
                                  active_page='idul-adha',
                                  content=rendered_content,
                                  is_admin=session.get('is_admin', False),
                                  settings=get_settings())"""
content = content.replace(pembagian_old, pembagian_new)

# 4. Peta Distribusi
peta_old = """    return render_template_string(BASE_LAYOUT,
                                  styles=STYLES_HTML,
                                  active_page='idul-adha',
                                  content=IDUL_ADHA_PETA_DISTRIBUSI_HTML,
                                  rt_list=rt_list,
                                  total_rt=total_rt,
                                  diserahkan_count=diserahkan_count,
                                  progress_percentage=progress_percentage,
                                  is_admin=session.get('is_admin', False),
                                  settings=get_settings())"""
peta_new = """    rendered_content = render_template_string(IDUL_ADHA_PETA_DISTRIBUSI_HTML,
                                              rt_list=rt_list,
                                              total_rt=total_rt,
                                              diserahkan_count=diserahkan_count,
                                              progress_percentage=progress_percentage,
                                              is_admin=session.get('is_admin', False),
                                              settings=get_settings())
    return render_template_string(BASE_LAYOUT,
                                  styles=STYLES_HTML,
                                  active_page='idul-adha',
                                  content=rendered_content,
                                  is_admin=session.get('is_admin', False),
                                  settings=get_settings())"""
content = content.replace(peta_old, peta_new)

with open("masjid-al-hijrah-63 - alternate - ( idcloudhost - others 5 fitur - Idul Adha Qurban ).py", "w") as f:
    f.write(content)
