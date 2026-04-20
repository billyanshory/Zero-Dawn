with open("sekolah-luar-biasa-90 ( idcloudhost - Nineteenth Layer of Quality Control - Data Privacy & Compliance (SLB-Specific) - v.89 - Opus 4.7 Ad. Think ).py", "r") as f:
    text = f.read()

search = """        doc.build(Story)
        buffer.seek(0)
        opaque_token = uuid.uuid4().hex[:12]"""

replace = """        uid = session.get('user_id')
        date_text = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        watermark_text = f"Diunduh oleh akun id={uid} pada {date_text}"
        req_id = getattr(g, 'request_id', None)

        Story.append(Spacer(1, 24))
        Story.append(Paragraph(f"<font size='7' color='#999999'>{watermark_text} (request_id={req_id})</font>", styles['NormalText']))

        doc.build(Story)
        buffer.seek(0)

        try:
            audit = IEPDownloadAudit(
                downloaded_by=uid,
                student_name=student_name,
                request_id=req_id,
                ip=request.headers.get('X-Forwarded-For', request.remote_addr)
            )
            db.session.add(audit)
            db.session.commit()
        except Exception:
            db.session.rollback()
            app.logger.error("Failed to audit IEP download", exc_info=True)

        opaque_token = uuid.uuid4().hex[:12]"""

if search in text:
    text = text.replace(search, replace)
    with open("sekolah-luar-biasa-90 ( idcloudhost - Nineteenth Layer of Quality Control - Data Privacy & Compliance (SLB-Specific) - v.89 - Opus 4.7 Ad. Think ).py", "w") as f:
        f.write(text)
    print("Success")
else:
    print("Search string not found")
