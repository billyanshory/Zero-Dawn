with open("sekolah-luar-biasa-90 ( idcloudhost - Nineteenth Layer of Quality Control - Data Privacy & Compliance (SLB-Specific) - v.89 - Opus 4.7 Ad. Think ).py", "r") as f:
    text = f.read()

search = """        now = datetime.datetime.now()
        total_purged = 0
        try:
            for key, (model, ts_col) in _RETENTION_MODEL_MAP.items():
                window = RETENTION_WINDOWS_DAYS.get(key)
                if not window:
                    continue
                cutoff = now - datetime.timedelta(days=window)
                purged = model.query.filter(getattr(model, ts_col) < cutoff).delete(synchronize_session=False)
                total_purged += purged
            db.session.commit()
            app.logger.info("Behavioral retention sweep purged %d rows", total_purged)
        except IntegrityError:
            db.session.rollback()
            app.logger.warning("Integrity error in apply_behavioral_retention", exc_info=True)
        except OperationalError:
            db.session.rollback()
            app.logger.warning("Operational error in apply_behavioral_retention", exc_info=True)
        except Exception:
            db.session.rollback()
            app.logger.error("Unexpected error in apply_behavioral_retention", exc_info=True)"""

replace = """        now = datetime.datetime.now()
        total_purged = 0
        for key, (model, ts_col) in _RETENTION_MODEL_MAP.items():
            try:
                window = RETENTION_WINDOWS_DAYS.get(key)
                if not window:
                    continue
                cutoff = now - datetime.timedelta(days=window)
                purged = model.query.filter(getattr(model, ts_col) < cutoff).delete(synchronize_session=False)
                db.session.commit()
                total_purged += purged
            except IntegrityError:
                db.session.rollback()
                app.logger.warning("Retention sweep skipped %s due to DB error.", key, exc_info=True)
            except OperationalError:
                db.session.rollback()
                app.logger.warning("Retention sweep skipped %s due to DB error.", key, exc_info=True)
            except Exception:
                db.session.rollback()
                app.logger.error("Retention sweep skipped %s due to DB error.", key, exc_info=True)
        app.logger.info("Behavioral retention sweep purged %d rows", total_purged)"""

if search in text:
    text = text.replace(search, replace)
    with open("sekolah-luar-biasa-90 ( idcloudhost - Nineteenth Layer of Quality Control - Data Privacy & Compliance (SLB-Specific) - v.89 - Opus 4.7 Ad. Think ).py", "w") as f:
        f.write(text)
    print("Success")
else:
    print("Search string not found")
