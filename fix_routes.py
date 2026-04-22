import re

filename = "masjid-al-hijrah-62 ( idcloudhost - fixing lay out - Idul Adha Qurban ).py"

with open(filename, "r") as f:
    content = f.read()

# I will use Python `replace` to be more precise instead of git merge diff

# Fix 1: finance
content = content.replace("""    if request.method == 'POST':
        if not session.get('is_admin'):
            return redirect(url_for('index'))

        if 'delete_id' in request.form:
            Finance.query.filter_by(id=request.form.get('delete_id', '')).delete()
        else:
            item = Finance(
                date=request.form.get('date', ''),
                type=request.form.get('type', ''),
                category=request.form.get('category', ''),
                description=request.form.get('description', ''),
                amount=int(request.form.get('amount', 0))
            )
            db.session.add(item)
        db.session.commit()
        return redirect(url_for('finance'))

    items = Finance.query.order_by(Finance.date.desc(), Finance.id.desc()).all()
    total_in = db.session.query(func.sum(Finance.amount)).filter_by(type='Pemasukan').scalar() or 0
    total_out = db.session.query(func.sum(Finance.amount)).filter_by(type='Pengeluaran').scalar() or 0
    balance = total_in - total_out""", """    if request.method == 'POST':
        if not session.get('is_admin'):
            return redirect(url_for('index'))

        try:
            if 'delete_id' in request.form:
                Finance.query.filter_by(id=request.form.get('delete_id', '')).delete()
            else:
                item = Finance(
                    date=request.form.get('date', ''),
                    type=request.form.get('type', ''),
                    category=request.form.get('category', ''),
                    description=request.form.get('description', ''),
                    amount=int(request.form.get('amount', 0))
                )
                db.session.add(item)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"DB Error: {e}")
        return redirect(url_for('finance'))

    try:
        items = Finance.query.order_by(Finance.date.desc(), Finance.id.desc()).all()
        total_in = db.session.query(func.sum(Finance.amount)).filter_by(type='Pemasukan').scalar() or 0
        total_out = db.session.query(func.sum(Finance.amount)).filter_by(type='Pengeluaran').scalar() or 0
        balance = total_in - total_out
    except Exception as e:
        app.logger.error(f"DB Error: {e}")
        items = []
        total_in = total_out = balance = 0""")

# Fix 2: agenda
content = content.replace("""    if request.method == 'POST':
        if not session.get('is_admin'):
            return redirect(url_for('index'))

        if 'delete_id' in request.form:
            Agenda.query.filter_by(id=request.form.get('delete_id', '')).delete()
        else:
            item = Agenda(
                date=request.form.get('date', ''),
                time=request.form.get('time', ''),
                title=request.form.get('title', ''),
                speaker=request.form.get('speaker', ''),
                type=request.form.get('type', '')
            )
            db.session.add(item)
        db.session.commit()
        return redirect(url_for('agenda'))

    items = Agenda.query.order_by(Agenda.date.desc(), Agenda.id.desc()).all()""", """    if request.method == 'POST':
        if not session.get('is_admin'):
            return redirect(url_for('index'))

        try:
            if 'delete_id' in request.form:
                Agenda.query.filter_by(id=request.form.get('delete_id', '')).delete()
            else:
                item = Agenda(
                    date=request.form.get('date', ''),
                    time=request.form.get('time', ''),
                    title=request.form.get('title', ''),
                    speaker=request.form.get('speaker', ''),
                    type=request.form.get('type', '')
                )
                db.session.add(item)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"DB Error: {e}")
        return redirect(url_for('agenda'))

    try:
        items = Agenda.query.order_by(Agenda.date.desc(), Agenda.id.desc()).all()
    except Exception as e:
        app.logger.error(f"DB Error: {e}")
        items = []""")

# Fix 3: booking
content = content.replace("""    if request.method == 'POST':
        if 'booking_id' in request.form:
            if not session.get('is_admin'):
                return redirect(url_for('index'))
            booking = Booking.query.get(request.form.get('booking_id', ''))
            if booking:
                booking.status = request.form.get('status', '')
        else:
            item = Booking(
                name=request.form.get('name', ''),
                date=request.form.get('date', ''),
                purpose=request.form.get('purpose', ''),
                type=request.form.get('type', ''),
                contact=request.form.get('contact', '')
            )
            db.session.add(item)
        db.session.commit()
        return redirect(url_for('booking'))

    items = Booking.query.order_by(Booking.created_at.desc()).all()""", """    if request.method == 'POST':
        try:
            if 'booking_id' in request.form:
                if not session.get('is_admin'):
                    return redirect(url_for('index'))
                booking = Booking.query.get(request.form.get('booking_id', ''))
                if booking:
                    booking.status = request.form.get('status', '')
            else:
                item = Booking(
                    name=request.form.get('name', ''),
                    date=request.form.get('date', ''),
                    purpose=request.form.get('purpose', ''),
                    type=request.form.get('type', ''),
                    contact=request.form.get('contact', '')
                )
                db.session.add(item)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"DB Error: {e}")
        return redirect(url_for('booking'))

    try:
        items = Booking.query.order_by(Booking.created_at.desc()).all()
    except Exception as e:
        app.logger.error(f"DB Error: {e}")
        items = []""")

# Fix 4: zakat
content = content.replace("""    if request.method == 'POST':
        item = Zakat(
            donor_name=request.form.get('donor_name', ''),
            type=request.form.get('type', ''),
            amount=request.form.get('amount', ''),
            notes=request.form.get('notes', ''),
        )
        db.session.add(item)
        db.session.commit()
        return redirect(url_for('zakat'))

    items = Zakat.query.order_by(Zakat.created_at.desc()).all()

    # Calculate simple totals based on amount string matching or manual parsing if standard
    total_zakat_fitrah = 0
    total_sapi = 0
    total_kambing = 0

    for z in items:
        if z.status != 'Verified':
            continue
        try:
            amt = int(''.join(filter(str.isdigit, z.amount)))
            if z.type == 'Zakat Fitrah':
                total_zakat_fitrah += amt
            elif z.type == 'Qurban Sapi':
                total_sapi += 1
            elif z.type == 'Qurban Kambing':
                total_kambing += 1
        except:
            pass""", """    if request.method == 'POST':
        try:
            item = Zakat(
                donor_name=request.form.get('donor_name', ''),
                type=request.form.get('type', ''),
                amount=request.form.get('amount', ''),
                notes=request.form.get('notes', ''),
            )
            db.session.add(item)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"DB Error: {e}")
        return redirect(url_for('zakat'))

    total_zakat_fitrah = 0
    total_sapi = 0
    total_kambing = 0

    try:
        items = Zakat.query.order_by(Zakat.created_at.desc()).all()
        for z in items:
            if z.status != 'Verified':
                continue
            try:
                amt = int(''.join(filter(str.isdigit, z.amount)))
                if z.type == 'Zakat Fitrah':
                    total_zakat_fitrah += amt
                elif z.type == 'Qurban Sapi':
                    total_sapi += 1
                elif z.type == 'Qurban Kambing':
                    total_kambing += 1
            except:
                pass
    except Exception as e:
        app.logger.error(f"DB Error: {e}")
        items = []""")

# Fix 5: gallery_dakwah
content = content.replace("""    if request.method == 'POST':
        if not can_edit:
            return redirect(url_for('index'))

        if 'delete_id' in request.form:
            GalleryDakwah.query.filter_by(id=request.form.get('delete_id', '')).delete()
        else:
            if 'image' in request.files:
                file = request.files['image']
                if file and allowed_file(file.filename):
                    saved_filename = compress_image(file, app.config['UPLOAD_FOLDER'])
                    item = GalleryDakwah(
                        title=request.form.get('title', ''),
                        image=saved_filename,
                        description=request.form.get('description', ''),
                        date=datetime.datetime.now().strftime("%Y-%m-%d")
                    )
                    db.session.add(item)
        db.session.commit()
        return redirect(url_for('gallery_dakwah'))

    items = GalleryDakwah.query.order_by(GalleryDakwah.created_at.desc()).all()""", """    if request.method == 'POST':
        if not can_edit:
            return redirect(url_for('index'))

        try:
            if 'delete_id' in request.form:
                GalleryDakwah.query.filter_by(id=request.form.get('delete_id', '')).delete()
            else:
                if 'image' in request.files:
                    file = request.files['image']
                    if file and allowed_file(file.filename):
                        saved_filename = compress_image(file, app.config['UPLOAD_FOLDER'])
                        item = GalleryDakwah(
                            title=request.form.get('title', ''),
                            image=saved_filename,
                            description=request.form.get('description', ''),
                            date=datetime.datetime.now().strftime("%Y-%m-%d")
                        )
                        db.session.add(item)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"DB Error: {e}")
        return redirect(url_for('gallery_dakwah'))

    try:
        items = GalleryDakwah.query.order_by(GalleryDakwah.created_at.desc()).all()
    except Exception as e:
        app.logger.error(f"DB Error: {e}")
        items = []""")

# Fix 6: suggestion
content = content.replace("""    if request.method == 'POST':
        if 'delete_id' in request.form:
            if not session.get('is_admin'):
                return redirect(url_for('index'))
            Suggestion.query.filter_by(id=request.form.get('delete_id', '')).delete()
        else:
            item = Suggestion(
                content=request.form.get('content', ''),
                date=datetime.datetime.now().strftime("%Y-%m-%d")
            )
            db.session.add(item)
        db.session.commit()
        return redirect(url_for('suggestion'))

    items = Suggestion.query.order_by(Suggestion.created_at.desc()).all()""", """    if request.method == 'POST':
        try:
            if 'delete_id' in request.form:
                if not session.get('is_admin'):
                    return redirect(url_for('index'))
                Suggestion.query.filter_by(id=request.form.get('delete_id', '')).delete()
            else:
                item = Suggestion(
                    content=request.form.get('content', ''),
                    date=datetime.datetime.now().strftime("%Y-%m-%d")
                )
                db.session.add(item)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"DB Error: {e}")
        return redirect(url_for('suggestion'))

    try:
        items = Suggestion.query.order_by(Suggestion.created_at.desc()).all()
    except Exception as e:
        app.logger.error(f"DB Error: {e}")
        items = []""")

with open(filename, "w") as f:
    f.write(content)
