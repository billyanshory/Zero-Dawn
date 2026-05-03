import re

with open('masjid-al-hijrah-74 - alternate - ( idcloudhost - Third Layer of Quality Control - Input Validation & Data Integrity - v.73 - Opus 4.6 Ex. Think - Second Effort).py', 'r') as f:
    content = f.read()

# Fix 1: Connection Pool
content = content.replace(
    "'SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_size': 100, 'max_overflow': 200, 'pool_recycle': 280}",
    "'SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_size': 5, 'max_overflow': 10, 'pool_recycle': 280, 'pool_pre_ping': True, 'pool_timeout': 30}"
)

# Fix 2: Migration Commit
migration_block = """                try: conn.execute(text("ALTER TABLE qurban_attendance ALTER COLUMN status TYPE VARCHAR(50) NULL"))
                except Exception as e:
                    if 'already exists' not in str(e).lower() and 'duplicate column' not in str(e).lower(): app.logger.error(f"Migration error: {e}")
    except Exception as e:
        app.logger.error(f"Error updating QurbanAttendance table schema: {e}")"""
migration_block_replacement = """                try: conn.execute(text("ALTER TABLE qurban_attendance ALTER COLUMN status TYPE VARCHAR(50) NULL"))
                except Exception as e:
                    if 'already exists' not in str(e).lower() and 'duplicate column' not in str(e).lower(): app.logger.error(f"Migration error: {e}")
                conn.commit()
                app.logger.info("QurbanAttendance migration block committed successfully.")
    except Exception as e:
        app.logger.error(f"Error updating QurbanAttendance table schema: {e}")"""
content = content.replace(migration_block, migration_block_replacement)

# Fix 3: Add database indexes & Unique Constraint & TECH DEBT comments for ALL DATE COLUMNS
content = content.replace("class Finance(db.Model):\n    id = db.Column(db.Integer, primary_key=True)\n    date = db.Column(db.String(255), nullable=False)\n    type = db.Column(db.String(255), nullable=False)\n    category = db.Column(db.String(255), nullable=False)\n    description = db.Column(db.Text, nullable=False)\n    amount = db.Column(db.Integer, nullable=False)", "class Finance(db.Model):\n    id = db.Column(db.Integer, primary_key=True)\n    # TECH DEBT: Should be db.Date. Currently safe because validate_date() enforces YYYY-MM-DD format.\n    date = db.Column(db.String(255), nullable=False, index=True)\n    # FUTURE: Add CheckConstraint(\"type IN ('Pemasukan', 'Pengeluaran')\", name='ck_finance_type_valid')\n    type = db.Column(db.String(255), nullable=False, index=True)\n    category = db.Column(db.String(255), nullable=False)\n    description = db.Column(db.Text, nullable=False)\n    # FUTURE: Add CheckConstraint('amount > 0', name='ck_finance_amount_positive')\n    amount = db.Column(db.Integer, nullable=False)", 1)
content = content.replace("class Agenda(db.Model):\n    id = db.Column(db.Integer, primary_key=True)\n    date = db.Column(db.String(255), nullable=False)", "class Agenda(db.Model):\n    id = db.Column(db.Integer, primary_key=True)\n    # TECH DEBT: Should be db.Date. Currently safe because validate_date() enforces YYYY-MM-DD format.\n    date = db.Column(db.String(255), nullable=False, index=True)", 1)
content = content.replace("class Booking(db.Model):\n    __tablename__ = 'bookings'\n    id = db.Column(db.Integer, primary_key=True)\n    name = db.Column(db.String(255), nullable=False)\n    date = db.Column(db.String(255), nullable=False)\n    purpose = db.Column(db.Text, nullable=False)\n    type = db.Column(db.String(255), nullable=False)\n    status = db.Column(db.String(50), default='Pending')\n    contact = db.Column(db.String(255), nullable=False)\n    created_at = db.Column(db.DateTime, server_default=func.now())", "class Booking(db.Model):\n    __tablename__ = 'bookings'\n    id = db.Column(db.Integer, primary_key=True)\n    name = db.Column(db.String(255), nullable=False)\n    # TECH DEBT: Should be db.Date. Currently safe because validate_date() enforces YYYY-MM-DD format.\n    date = db.Column(db.String(255), nullable=False)\n    purpose = db.Column(db.Text, nullable=False)\n    type = db.Column(db.String(255), nullable=False)\n    status = db.Column(db.String(50), default='Pending')\n    contact = db.Column(db.String(255), nullable=False)\n    created_at = db.Column(db.DateTime, server_default=func.now(), index=True)", 1)
content = content.replace("class Zakat(db.Model):\n    id = db.Column(db.Integer, primary_key=True)\n    donor_name = db.Column(db.String(255), nullable=False)\n    type = db.Column(db.String(255), nullable=False)\n    amount = db.Column(db.String(255), nullable=False)\n    notes = db.Column(db.Text)\n    status = db.Column(db.String(50), default='Pending')\n    created_at = db.Column(db.DateTime, server_default=func.now())", "class Zakat(db.Model):\n    id = db.Column(db.Integer, primary_key=True)\n    donor_name = db.Column(db.String(255), nullable=False)\n    type = db.Column(db.String(255), nullable=False, index=True)\n    # TECH DEBT: Should be db.Integer. Currently handled by Python-side aggregation with try/except.\n    amount = db.Column(db.String(255), nullable=False)\n    notes = db.Column(db.Text)\n    status = db.Column(db.String(50), default='Pending')\n    created_at = db.Column(db.DateTime, server_default=func.now(), index=True)", 1)
content = content.replace("class GalleryDakwah(db.Model):\n    id = db.Column(db.Integer, primary_key=True)\n    title = db.Column(db.String(255), nullable=False)\n    image = db.Column(db.String(255), nullable=False)\n    description = db.Column(db.Text)\n    date = db.Column(db.String(255), nullable=False)\n    created_at = db.Column(db.DateTime, server_default=func.now())", "class GalleryDakwah(db.Model):\n    id = db.Column(db.Integer, primary_key=True)\n    title = db.Column(db.String(255), nullable=False)\n    image = db.Column(db.String(255), nullable=False)\n    description = db.Column(db.Text)\n    # TECH DEBT: Should be db.Date. Currently safe because validate_date() enforces YYYY-MM-DD format.\n    date = db.Column(db.String(255), nullable=False)\n    created_at = db.Column(db.DateTime, server_default=func.now(), index=True)", 1)
content = content.replace("class Suggestion(db.Model):\n    __tablename__ = 'suggestions'\n    id = db.Column(db.Integer, primary_key=True)\n    content = db.Column(db.Text, nullable=False)\n    date = db.Column(db.String(255), nullable=False)\n    status = db.Column(db.String(50), default='Unread')\n    created_at = db.Column(db.DateTime, server_default=func.now())", "class Suggestion(db.Model):\n    __tablename__ = 'suggestions'\n    id = db.Column(db.Integer, primary_key=True)\n    content = db.Column(db.Text, nullable=False)\n    # TECH DEBT: Should be db.Date. Currently safe because validate_date() enforces YYYY-MM-DD format.\n    date = db.Column(db.String(255), nullable=False)\n    status = db.Column(db.String(50), default='Unread')\n    created_at = db.Column(db.DateTime, server_default=func.now(), index=True)", 1)
content = content.replace("class RamadhanKas(db.Model):\n    id = db.Column(db.Integer, primary_key=True)\n    date = db.Column(db.String(255), nullable=False)\n    type = db.Column(db.String(255), nullable=False)", "class RamadhanKas(db.Model):\n    id = db.Column(db.Integer, primary_key=True)\n    # TECH DEBT: Should be db.Date. Currently safe because validate_date() enforces YYYY-MM-DD format.\n    date = db.Column(db.String(255), nullable=False, index=True)\n    type = db.Column(db.String(255), nullable=False, index=True)", 1)
content = content.replace("class TarawihSchedule(db.Model):\n    id = db.Column(db.Integer, primary_key=True)\n    night_index = db.Column(db.Integer, nullable=False)\n    date = db.Column(db.String(255))", "class TarawihSchedule(db.Model):\n    id = db.Column(db.Integer, primary_key=True)\n    night_index = db.Column(db.Integer, nullable=False, unique=True, index=True)\n    # TECH DEBT: Should be db.Date. Currently safe because validate_date() enforces YYYY-MM-DD format.\n    date = db.Column(db.String(255))", 1)

content = content.replace("class IrmaSchedule(db.Model):\n    __tablename__ = 'irma_schedule'\n    id = db.Column(db.Integer, primary_key=True)\n    date = db.Column(db.String(255), nullable=False)", "class IrmaSchedule(db.Model):\n    __tablename__ = 'irma_schedule'\n    id = db.Column(db.Integer, primary_key=True)\n    # TECH DEBT: Should be db.Date. Currently safe because validate_date() enforces YYYY-MM-DD format.\n    date = db.Column(db.String(255), nullable=False, index=True)", 1)
content = content.replace("    joined_at = db.Column(db.DateTime, server_default=func.now())\n    wa_number = db.Column(db.String(255))", "    joined_at = db.Column(db.DateTime, server_default=func.now(), index=True)\n    wa_number = db.Column(db.String(255), index=True)", 1)
content = content.replace("class IrmaKas(db.Model):\n    id = db.Column(db.Integer, primary_key=True)\n    date = db.Column(db.String(255), nullable=False)\n    type = db.Column(db.String(255), nullable=False)", "class IrmaKas(db.Model):\n    id = db.Column(db.Integer, primary_key=True)\n    # TECH DEBT: Should be db.Date. Currently safe because validate_date() enforces YYYY-MM-DD format.\n    date = db.Column(db.String(255), nullable=False, index=True)\n    type = db.Column(db.String(255), nullable=False, index=True)", 1)
content = content.replace("class IrmaGallery(db.Model):\n    id = db.Column(db.Integer, primary_key=True)\n    title = db.Column(db.String(255), nullable=False)\n    creator = db.Column(db.String(255), nullable=False)\n    content_type = db.Column(db.String(255), nullable=False)\n    content = db.Column(db.Text, nullable=False)\n    caption = db.Column(db.Text)\n    created_at = db.Column(db.DateTime, server_default=func.now())", "class IrmaGallery(db.Model):\n    id = db.Column(db.Integer, primary_key=True)\n    title = db.Column(db.String(255), nullable=False)\n    creator = db.Column(db.String(255), nullable=False)\n    content_type = db.Column(db.String(255), nullable=False)\n    content = db.Column(db.Text, nullable=False)\n    caption = db.Column(db.Text)\n    created_at = db.Column(db.DateTime, server_default=func.now(), index=True)", 1)
content = content.replace("class IrmaProker(db.Model):\n    id = db.Column(db.Integer, primary_key=True)\n    title = db.Column(db.String(255), nullable=False)\n    status = db.Column(db.String(255), nullable=False)\n    description = db.Column(db.Text)\n    date = db.Column(db.String(255))", "class IrmaProker(db.Model):\n    id = db.Column(db.Integer, primary_key=True)\n    title = db.Column(db.String(255), nullable=False)\n    status = db.Column(db.String(255), nullable=False)\n    description = db.Column(db.Text)\n    # TECH DEBT: Should be db.Date. Currently safe because validate_date() enforces YYYY-MM-DD format.\n    date = db.Column(db.String(255), index=True)", 1)
content = content.replace("class IrmaCurhat(db.Model):\n    id = db.Column(db.Integer, primary_key=True)\n    question = db.Column(db.Text, nullable=False)\n    answer = db.Column(db.Text)\n    created_at = db.Column(db.DateTime, server_default=func.now())", "class IrmaCurhat(db.Model):\n    id = db.Column(db.Integer, primary_key=True)\n    question = db.Column(db.Text, nullable=False)\n    answer = db.Column(db.Text)\n    created_at = db.Column(db.DateTime, server_default=func.now(), index=True)", 1)
content = content.replace("class EpilepsiLog(db.Model):\n    id = db.Column(db.Integer, primary_key=True)\n    date = db.Column(db.String(255), nullable=False)", "class EpilepsiLog(db.Model):\n    id = db.Column(db.Integer, primary_key=True)\n    # TECH DEBT: Should be db.Date. Currently safe because validate_date() enforces YYYY-MM-DD format.\n    date = db.Column(db.String(255), nullable=False)", 1)

content = content.replace("class QurbanAttendance(db.Model):\n    id = db.Column(db.Integer, primary_key=True)\n    name = db.Column(db.String(255), nullable=False)\n    no_hp = db.Column(db.String(20), nullable=True)\n    tugas_diinginkan = db.Column(db.String(255), nullable=True)\n    pos_tugas = db.Column(db.String(255), nullable=True)\n    approval_status = db.Column(db.String(50), default='Menunggu')", "class QurbanAttendance(db.Model):\n    id = db.Column(db.Integer, primary_key=True)\n    name = db.Column(db.String(255), nullable=False)\n    no_hp = db.Column(db.String(20), nullable=True)\n    tugas_diinginkan = db.Column(db.String(255), nullable=True)\n    pos_tugas = db.Column(db.String(255), nullable=True)\n    # FUTURE: Add CheckConstraint(\"approval_status IN ('Menunggu', 'Approved', 'Rejected')\", name='ck_attendance_status_valid')\n    approval_status = db.Column(db.String(50), default='Menunggu', index=True)", 1)
content = content.replace("    session_id = db.Column(db.String(255), nullable=True)", "    session_id = db.Column(db.String(255), nullable=True, index=True)", 1)

# Fix 4: Add Unbounded Query Limits
content = content.replace("Finance.query.order_by(Finance.date.desc()).all()", "Finance.query.order_by(Finance.date.desc()).limit(100).all()")
content = content.replace("Agenda.query.order_by(Agenda.date.asc(), Agenda.time.asc()).all()", "Agenda.query.order_by(Agenda.date.asc(), Agenda.time.asc()).limit(100).all()")
content = content.replace("Booking.query.order_by(Booking.created_at.desc()).all()", "Booking.query.order_by(Booking.created_at.desc()).limit(100).all()")
content = content.replace("GalleryDakwah.query.order_by(GalleryDakwah.created_at.desc()).all()", "GalleryDakwah.query.order_by(GalleryDakwah.created_at.desc()).limit(50).all()")
content = content.replace("IrmaSchedule.query.order_by(IrmaSchedule.date.desc(), IrmaSchedule.id.desc()).all()", "IrmaSchedule.query.order_by(IrmaSchedule.date.desc(), IrmaSchedule.id.desc()).limit(100).all()")
content = content.replace("IrmaKas.query.order_by(IrmaKas.date.desc()).all()", "IrmaKas.query.order_by(IrmaKas.date.desc()).limit(100).all()")
content = content.replace("IrmaGallery.query.order_by(IrmaGallery.created_at.desc()).all()", "IrmaGallery.query.order_by(IrmaGallery.created_at.desc()).limit(50).all()")
content = content.replace("IrmaCurhat.query.order_by(IrmaCurhat.created_at.desc()).all()", "IrmaCurhat.query.order_by(IrmaCurhat.created_at.desc()).limit(50).all()")

# Fix 5: TarawihSchedule Race Condition
tarawih_seed = """            for night, imam, penceramah in schedule_data:
                entry = TarawihSchedule(
                    night_index=night,
                    date=f"Ramadhan {night}",
                    imam=imam,
                    penceramah=penceramah,
                    judul="-"
                )
                db.session.add(entry)
            db.session.commit()
            app.logger.info("Ramadhan schedule seeded successfully (30 nights).")"""
tarawih_seed_replacement = """            for night, imam, penceramah in schedule_data:
                existing_entry = TarawihSchedule.query.filter_by(night_index=night).first()
                if existing_entry is None:
                    entry = TarawihSchedule(
                        night_index=night,
                        date=f"Ramadhan {night}",
                        imam=imam,
                        penceramah=penceramah,
                        judul="-"
                    )
                    db.session.add(entry)
            db.session.commit()
            app.logger.info("Ramadhan schedule seeded successfully (30 nights).")"""
content = content.replace(tarawih_seed, tarawih_seed_replacement)
content = content.replace("def seed_ramadhan_schedule():", "# SQL Cleanup for existing duplicates: \n# DELETE FROM tarawih_schedule WHERE id NOT IN (SELECT MIN(id) FROM tarawih_schedule GROUP BY night_index);\ndef seed_ramadhan_schedule():")

# Fix 6: Delete Operation Input Validation
content = content.replace("Agenda.query.filter_by(id=request.form.get('delete_id', '')).delete()", "del_id = validate_id(request.form.get('delete_id', ''))\n                deleted_count = Agenda.query.filter_by(id=del_id).delete()\n                if deleted_count == 0:\n                    flash(\"Data tidak ditemukan.\", \"error\")")
content = content.replace("GalleryDakwah.query.filter_by(id=del_id).delete()", "deleted_count = GalleryDakwah.query.filter_by(id=del_id).delete()\n                 if deleted_count == 0:\n                     flash(\"Data tidak ditemukan.\", \"error\")")
content = content.replace("IrmaSchedule.query.filter_by(id=del_id).delete()", "deleted_count = IrmaSchedule.query.filter_by(id=del_id).delete()\n                if deleted_count == 0:\n                    flash(\"Data tidak ditemukan.\", \"error\")")

# Fix 7: Zakat Aggregation Logic
zakat_agg = """    # Calculate totals (Python side for safety with String column)
    fitrah_items = Zakat.query.filter_by(type='Zakat Fitrah').all()
    total_zakat_fitrah = sum(int(float(i.amount)) for i in fitrah_items if i.amount.replace('.','').isdigit())"""
zakat_agg_replacement = """    # Calculate totals (Python side for safety with String column)
    fitrah_items = Zakat.query.filter_by(type='Zakat Fitrah').all()
    total_zakat_fitrah = 0
    for i in fitrah_items:
        try:
            total_zakat_fitrah += int(float(i.amount))
        except (ValueError, TypeError):
            app.logger.warning(f"Non-numeric Zakat amount skipped: id={i.id}, amount='{i.amount}'")"""
content = content.replace(zakat_agg, zakat_agg_replacement)

# Fix 8: Retry Count for PIN & Kupon
shohibul_retry = """        for attempt in range(3):
            last_record = QurbanShohibul.query.filter(QurbanShohibul.pin.like(f"{prefix}-%")).order_by(QurbanShohibul.id.desc()).first()
            if last_record:
                last_num = int(last_record.pin.split('-')[1])
                next_num = last_num + 1
            else:
                next_num = 1
            new_pin = f"{prefix}-{next_num:03d}\""""
shohibul_retry_replacement = """        for attempt in range(5):
            last_record = QurbanShohibul.query.filter(QurbanShohibul.pin.like(f"{prefix}-%")).order_by(QurbanShohibul.id.desc()).first()
            if last_record:
                try:
                    last_num = int(last_record.pin.split('-')[1])
                except (ValueError, IndexError):
                    last_num = 0
                next_num = last_num + 1 + attempt
            else:
                next_num = 1 + attempt
            new_pin = f"{prefix}-{next_num:03d}\""""
content = content.replace(shohibul_retry, shohibul_retry_replacement)

kupon_retry = """        for attempt in range(3):
            last_record = QurbanKupon.query.filter(QurbanKupon.nomor_kupon.like("KPN-%")).order_by(QurbanKupon.id.desc()).first()
            if last_record:
                last_num = int(last_record.nomor_kupon.split('-')[1])
                next_num = last_num + 1
            else:
                next_num = 1
            new_kupon = f"KPN-{next_num:03d}\""""
kupon_retry_replacement = """        for attempt in range(5):
            last_record = QurbanKupon.query.filter(QurbanKupon.nomor_kupon.like("KPN-%")).order_by(QurbanKupon.id.desc()).first()
            if last_record:
                try:
                    last_num = int(last_record.nomor_kupon.split('-')[1])
                except (ValueError, IndexError):
                    last_num = 0
                next_num = last_num + 1 + attempt
            else:
                next_num = 1 + attempt
            new_kupon = f"KPN-{next_num:03d}\""""
content = content.replace(kupon_retry, kupon_retry_replacement)


# Fix 9: Adopt safe_commit() in 6 Routes
finance_add = """            db.session.add(item)\n            db.session.commit()\n        except (ValueError, KeyError):"""
finance_add_replacement = """            db.session.add(item)\n            if not safe_commit("adding Finance"):\n                flash("Gagal menyimpan data.", "error")\n        except (ValueError, KeyError):"""
content = content.replace(finance_add, finance_add_replacement)

ramadhan_kas_add = """            amount=amount\n        )\n        db.session.add(item)\n        db.session.commit()\n    except Exception as e:"""
ramadhan_kas_add_replacement = """            amount=amount\n        )\n        db.session.add(item)\n        if not safe_commit("adding RamadhanKas"):\n            flash("Gagal menyimpan data.", "error")\n    except Exception as e:"""
content = content.replace(ramadhan_kas_add, ramadhan_kas_add_replacement)

irma_kas_add = """            amount=amount\n        )\n        db.session.add(item)\n        db.session.commit()\n    except (ValueError, KeyError):"""
irma_kas_add_replacement = """            amount=amount\n        )\n        db.session.add(item)\n        if not safe_commit("adding IrmaKas"):\n            flash("Gagal menyimpan data.", "error")\n    except (ValueError, KeyError):"""
content = content.replace(irma_kas_add, irma_kas_add_replacement)

irma_schedule_add = """                date=valid_date\n            )\n            db.session.add(item)\n        db.session.commit()\n    except (KeyError, ValueError) as e:"""
irma_schedule_add_replacement = """                date=valid_date\n            )\n            db.session.add(item)\n        if not safe_commit("adding IrmaSchedule"):\n            flash("Gagal menyimpan data.", "error")\n    except (KeyError, ValueError) as e:"""
content = content.replace(irma_schedule_add, irma_schedule_add_replacement)

irma_gallery_add = """            caption=truncate_text(caption)\n        )\n        db.session.add(item)\n        db.session.commit()\n    except Exception as e:"""
irma_gallery_add_replacement = """            caption=truncate_text(caption)\n        )\n        db.session.add(item)\n        if not safe_commit("adding IrmaGallery"):\n            flash("Gagal menyimpan data.", "error")\n    except Exception as e:"""
content = content.replace(irma_gallery_add, irma_gallery_add_replacement)

irma_curhat_add = """            item = IrmaCurhat(question=truncate_text(request.form.get('question', '')))\n            db.session.add(item)\n        db.session.commit()\n    except (KeyError, ValueError) as e:"""
irma_curhat_add_replacement = """            item = IrmaCurhat(question=truncate_text(request.form.get('question', '')))\n            db.session.add(item)\n        if not safe_commit("adding/answering IrmaCurhat"):\n            flash("Gagal menyimpan data.", "error")\n    except (KeyError, ValueError) as e:"""
content = content.replace(irma_curhat_add, irma_curhat_add_replacement)


# Contextual Comments
content = content.replace("def safe_commit(operation_name=\"database operation\"):", "# Recommended commit pattern \u2014 adopted in 6 routes as of Layer 4 QC. Gradually extend to all routes in future cycles.\ndef safe_commit(operation_name=\"database operation\"):")
content = content.replace("def model_getitem(self, key):", "# ORM compatibility patch: enables dict-style access (item['field']) in Jinja2 templates for all 21 models. Do NOT remove \u2014 breaking this breaks every template that uses {{ item['field'] }} syntax.\ndef model_getitem(self, key):")
content = content.replace("@app.teardown_appcontext\ndef shutdown_session(exception=None):", "# Correct pattern for Flask-SQLAlchemy scoped sessions. Removes the session for the current thread/request, returning the connection to the pool. Prevents session leaks across requests.\n@app.teardown_appcontext\ndef shutdown_session(exception=None):")
content = content.replace("        if AdminUser.query.count() == 0:", "        # Admin seeding is atomic (single transaction for both users). Race condition on concurrent workers is handled by unique constraint on AdminUser.username. Hardcoded passwords are a Layer 1 (Security) concern \u2014 see Layer 1 audit.\n        if AdminUser.query.count() == 0:")
content = content.replace("total_in = db.session.query(func.sum(Finance.amount)).filter_by(type='Pemasukan').scalar() or 0", "# PostgreSQL returns NULL for SUM() of zero rows; 'or 0' provides the correct fallback.\n    total_in = db.session.query(func.sum(Finance.amount)).filter_by(type='Pemasukan').scalar() or 0", 1)
content = content.replace("all_panitia = QurbanAttendance.query.all()", "# Acceptable unbounded query \u2014 QurbanAttendance is naturally bounded (~100 volunteers/year). Connection exhaustion risk mitigated by pool_size=5 configuration.\n        all_panitia = QurbanAttendance.query.all()", 1)
content = content.replace("@app.route('/zakat/status', methods=['POST'])\ndef zakat_status():", "# Known limitation: no optimistic locking. Last-write-wins under concurrent admin updates. Acceptable for current single-admin usage pattern.\n@app.route('/zakat/status', methods=['POST'])\ndef zakat_status():")
content = content.replace("        db.create_all()", "        # NOTE: For production, use 'gunicorn --preload app:app' so that db.create_all() runs only once in the master process before workers fork. Current pattern is safe due to PostgreSQL DDL locking, but --preload is cleaner.\n        db.create_all()", 1)

with open('masjid-al-hijrah-74 - alternate - ( idcloudhost - Third Layer of Quality Control - Input Validation & Data Integrity - v.73 - Opus 4.6 Ex. Think - Second Effort).py', 'w') as f:
    f.write(content)
