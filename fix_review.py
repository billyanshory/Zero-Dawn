import re

with open("masjid-al-hijrah-64 ( idcloudhost - fixing 4 fitur - Idul Adha Qurban ).py", "r") as f:
    content = f.read()

# Fix 1: Database Column length for NIK (now Nama)
content = content.replace("nik = db.Column(db.String(16), nullable=False)", "nik = db.Column(db.String(255), nullable=False)")

# Fix 2: Schema Migration logic (Wait, I DID apply it in patch_db.py but wait, maybe I applied it to the test_run2.py file only? No, I applied it to the original file. Let me double check if `db.metadata.drop_all` is there. I will just enforce it using exact replace here)
old_db = """with app.app_context():
    db.create_all()"""

new_db = """with app.app_context():
    try:
        db.session.execute(text('SELECT verified_by_admin FROM qurban_attendance LIMIT 1'))
    except Exception as e:
        db.session.rollback()
        try:
            QurbanAttendance.__table__.drop(db.engine, checkfirst=True)
            print("Dropped QurbanAttendance table for schema migration")
        except:
            pass
    db.create_all()"""

if old_db in content:
    content = content.replace(old_db, new_db)

# Fix 3: Graceful error for admin_qurban_peta
old_err = """    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in peta distribusi: {e}")
        return "Internal Server Error", 500"""

new_err = """    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in admin peta distribusi: {e}")
        return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, active_page='idul-adha', content="<div class='min-h-screen flex items-center justify-center p-4 pt-24'><div class='bg-white p-8 rounded-3xl shadow-xl max-w-md text-center'><i class='fas fa-exclamation-triangle text-4xl text-red-500 mb-4'></i><h3 class='text-xl font-bold text-gray-800 mb-2'>Kesalahan Sistem</h3><p class='text-gray-600 mb-4'>Data peta distribusi belum dikonfigurasi atau terjadi kesalahan database.</p><a href='/idul-adha' class='inline-block bg-[#1B4332] text-white px-6 py-2 rounded-xl font-bold'>Kembali ke Dashboard</a></div></div>", is_admin=True, settings=get_settings())"""

if old_err in content:
    content = content.replace(old_err, new_err)

# Fix 4: Missing Top padding
templates = [
    'IDUL_ADHA_LAPORAN_HTML = """',
    'IDUL_ADHA_LAPORAN_HTML = \'\'\'',
    'IDUL_ADHA_HEWAN_ADMIN_HTML = """',
    'IDUL_ADHA_HEWAN_ADMIN_HTML = \'\'\'',
    'IDUL_ADHA_PEMBAGIAN_ADMIN_HTML = """',
    'IDUL_ADHA_PEMBAGIAN_ADMIN_HTML = \'\'\'',
    'IDUL_ADHA_PETA_DISTRIBUSI_HTML = """',
    'IDUL_ADHA_PETA_DISTRIBUSI_HTML = \'\'\'',
    'IDUL_ADHA_PANDUAN_HTML = """',
    'IDUL_ADHA_PANDUAN_HTML = \'\'\'',
]

for tmpl in templates:
    # We want to find the first `<div class="min-h-screen bg-[#F5F0E8] font-sans pb-20">`
    # or similar after the template start.
    idx = content.find(tmpl)
    if idx != -1:
        start_search = idx
        end_search = start_search + 500
        # Replace `pb-20` or `pb-20 flex` with `pt-20 md:pt-24 pb-20` if not already there
        # Wait, some already have pt-24 md:pt-28.
        segment = content[start_search:end_search]
        if 'pt-20' not in segment and 'pt-24' not in segment:
            new_seg = segment.replace('pb-20"', 'pt-20 md:pt-24 pb-20"')
            new_seg = new_seg.replace('pb-20 flex', 'pt-20 md:pt-24 pb-20 flex')
            content = content[:start_search] + new_seg + content[end_search:]

# Fix 5: rename misleading missing_rts
content = content.replace('missing_rts = [s.rt_identifier for s in slots if not s.is_locked]', 'pending_rts = [s.rt_identifier for s in slots if not s.is_locked]')
content = content.replace('missing_rts=missing_rts', 'pending_rts=pending_rts')
content = content.replace('{% if missing_rts %}', '{% if pending_rts %}')
content = content.replace('{{ missing_rts|join(', '{{ pending_rts|join(')
content = content.replace('missing_rts=', 'pending_rts=')

with open("masjid-al-hijrah-64 ( idcloudhost - fixing 4 fitur - Idul Adha Qurban ).py", "w") as f:
    f.write(content)
