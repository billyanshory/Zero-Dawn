import sys

filepath = "kampus-stie-samarinda-0 ( idcloudhost - 3 dashboard utama - tu, mahasiswa dan dosen ).py"

with open(filepath, 'r') as f:
    content = f.read()

target = "for model in [Finance, Agenda, Booking, Zakat, GalleryDakwah, Suggestion, RamadhanKas, \n              TarawihSchedule, IrmaSchedule, IrmaMember, IrmaKas, IrmaGallery, \n              IrmaProker, IrmaCurhat, EpilepsiLog, AppSettings]:"

replacement = "for model in [Finance, Agenda, Booking, Zakat, GalleryDakwah, Suggestion, RamadhanKas, \n              TarawihSchedule, IrmaSchedule, IrmaMember, IrmaKas, IrmaGallery, \n              IrmaProker, IrmaCurhat, EpilepsiLog, AppSettings, SuratOtomatis, PendaftaranPMB, TagihanKuliah, JadwalKuliah, User, LaciArsip]:"

if target in content:
    new_content = content.replace(target, replacement)
    with open(filepath, 'w') as f:
        f.write(new_content)
    print("model_getitem array updated.")
else:
    print("Target not found.")
