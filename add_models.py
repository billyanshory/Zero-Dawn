import re

filename = "masjid-al-hijrah-62 ( idcloudhost - fixing lay out - Idul Adha Qurban ).py"

with open(filename, "r") as f:
    content = f.read()

models = """
class QurbanStats(db.Model):
    __tablename__ = 'qurban_stats'
    id = db.Column(db.Integer, primary_key=True)
    total_cattle = db.Column(db.Integer, default=0, nullable=False)
    total_goat = db.Column(db.Integer, default=0, nullable=False)
    total_meat_weight_kg = db.Column(db.Float, default=0.0, nullable=False)
    total_packages_prepared = db.Column(db.Integer, default=0, nullable=False)
    total_packages_distributed = db.Column(db.Integer, default=0, nullable=False)
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())

class QurbanAnimal(db.Model):
    __tablename__ = 'qurban_animals'
    id = db.Column(db.Integer, primary_key=True)
    animal_type = db.Column(db.String(50), nullable=False) # sapi, kambing
    queue_number = db.Column(db.Integer, nullable=False)
    sohibul_name = db.Column(db.String(255), nullable=False)
    wa_number = db.Column(db.String(50), nullable=False)
    pin = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(50), default='menunggu_giliran', nullable=False) # menunggu_giliran, sedang_disembelih, proses_pencacahan, siap_diambil
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())

class DistribusiSlot(db.Model):
    __tablename__ = 'distribusi_slots'
    id = db.Column(db.Integer, primary_key=True)
    rt_identifier = db.Column(db.String(50), nullable=False)
    time_start = db.Column(db.String(10), nullable=False) # HH:MM
    time_end = db.Column(db.String(10), nullable=False) # HH:MM
    total_quota = db.Column(db.Integer, default=0, nullable=False)
    distributed_count = db.Column(db.Integer, default=0, nullable=False)
    is_locked = db.Column(db.Boolean, default=False, nullable=False)
    handler_name = db.Column(db.String(255))
    handover_time = db.Column(db.DateTime)

class DistribusiKupon(db.Model):
    __tablename__ = 'distribusi_kupon'
    id = db.Column(db.Integer, primary_key=True)
    slot_id = db.Column(db.Integer, db.ForeignKey('distribusi_slots.id', ondelete='CASCADE'), nullable=False)
    nik = db.Column(db.String(16), nullable=False)
    coupon_number = db.Column(db.String(50), nullable=False)
    is_claimed = db.Column(db.Boolean, default=False, nullable=False)
    claimed_at = db.Column(db.DateTime)
"""

# Find a good place to inject models. Let's find QurbanAttendance
# and insert it right after.
insertion_point = "class QurbanAttendance(db.Model):"

parts = content.split(insertion_point)
if len(parts) == 2:
    new_content = parts[0] + insertion_point + parts[1].split("def get_settings():")[0] + "\n" + models + "\n" + "def get_settings():" + parts[1].split("def get_settings():")[1]

    # We also need to add them to model_getitem patch
    patch_find = "for model in [Finance, Agenda, Booking, Zakat, GalleryDakwah, Suggestion, RamadhanKas, \n              TarawihSchedule, IrmaSchedule, IrmaMember, IrmaKas, IrmaGallery, \n              IrmaProker, IrmaCurhat, EpilepsiLog, AppSettings, QurbanAttendance]:"
    patch_replace = "for model in [Finance, Agenda, Booking, Zakat, GalleryDakwah, Suggestion, RamadhanKas, \n              TarawihSchedule, IrmaSchedule, IrmaMember, IrmaKas, IrmaGallery, \n              IrmaProker, IrmaCurhat, EpilepsiLog, AppSettings, QurbanAttendance, \n              QurbanStats, QurbanAnimal, DistribusiSlot, DistribusiKupon]:"

    new_content = new_content.replace(patch_find, patch_replace)

    with open(filename, "w") as f:
        f.write(new_content)
    print("Models injected successfully.")
else:
    print("Could not find insertion point.")
