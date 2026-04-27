import re

with open("masjid-al-hijrah-63 - alternate - ( idcloudhost - others 5 fitur - Idul Adha Qurban ).py", "r") as f:
    content = f.read()

models = """
class QurbanReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    total_sapi = db.Column(db.Integer, default=12)
    total_kambing = db.Column(db.Integer, default=20)
    estimasi_daging = db.Column(db.Integer, default=1500)
    paket_terdistribusi = db.Column(db.Integer, default=450)
    paket_total = db.Column(db.Integer, default=1000)

class QurbanShohibul(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pin = db.Column(db.String(20), unique=True, nullable=False)
    jenis_hewan = db.Column(db.String(50), nullable=False) # 'Sapi' or 'Kambing'
    nama_shohibul = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='Menunggu Giliran') # 'Menunggu Giliran', 'Sedang Disembelih', 'Proses Pencacahan', 'Jatah Sohibul Siap Diambil'
    created_at = db.Column(db.DateTime, server_default=func.now())

class QurbanKupon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nomor_kupon = db.Column(db.String(20), unique=True, nullable=False)
    nama_penerima = db.Column(db.String(255), nullable=False)
    rt = db.Column(db.String(50), nullable=False)
    waktu_pengambilan = db.Column(db.String(255), nullable=False)
    lokasi_pengambilan = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now())

class QurbanRT(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nomor_card = db.Column(db.String(20), nullable=False)
    rt_name = db.Column(db.String(50), nullable=False)
    nama_ketua_rt = db.Column(db.String(255), nullable=False)
    alokasi = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), default='Menunggu') # 'Menunggu' or 'Diserahkan'
"""

# Insert models before get_settings
if 'class QurbanReport' not in content:
    content = re.sub(r'def get_settings\(\):', models + '\ndef get_settings():', content, count=1)

# Update model_getitem list
if 'QurbanReport' not in content:
    old_list = "for model in [Finance, Agenda, Booking, Zakat, GalleryDakwah, Suggestion, RamadhanKas, \n              TarawihSchedule, IrmaSchedule, IrmaMember, IrmaKas, IrmaGallery, \n              IrmaProker, IrmaCurhat, EpilepsiLog, AppSettings, QurbanAttendance]:"
    new_list = "for model in [Finance, Agenda, Booking, Zakat, GalleryDakwah, Suggestion, RamadhanKas, \n              TarawihSchedule, IrmaSchedule, IrmaMember, IrmaKas, IrmaGallery, \n              IrmaProker, IrmaCurhat, EpilepsiLog, AppSettings, QurbanAttendance, \n              QurbanReport, QurbanShohibul, QurbanKupon, QurbanRT]:"
    content = content.replace(old_list, new_list)

with open("masjid-al-hijrah-63 - alternate - ( idcloudhost - others 5 fitur - Idul Adha Qurban ).py", "w") as f:
    f.write(content)
