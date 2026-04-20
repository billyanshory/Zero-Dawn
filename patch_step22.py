with open("sekolah-luar-biasa-90 ( idcloudhost - Nineteenth Layer of Quality Control - Data Privacy & Compliance (SLB-Specific) - v.89 - Opus 4.7 Ad. Think ).py", "r") as f:
    text = f.read()

search = """        if os.environ.get('FLASK_INIT_DB') and os.environ.get('FLASK_ENV', '').lower() == 'development':
            app.logger.info("Dev-only bootstrap: running db.create_all() and seed_slb_data()")
            db.create_all()
            seed_slb_data()"""

replace = """        if os.environ.get('FLASK_INIT_DB') and os.environ.get('FLASK_ENV', '').lower() == 'development':
            if os.getenv('PRODUCTION') == '1' or os.getenv('IDCLOUDHOST') == '1':
                raise RuntimeError("Refusing to run db.create_all() with production indicators present.")
            app.logger.info("Dev-only bootstrap: running db.create_all() and seed_slb_data()")
            db.create_all()
            seed_slb_data()"""

if search in text:
    text = text.replace(search, replace)
    with open("sekolah-luar-biasa-90 ( idcloudhost - Nineteenth Layer of Quality Control - Data Privacy & Compliance (SLB-Specific) - v.89 - Opus 4.7 Ad. Think ).py", "w") as f:
        f.write(text)
    print("Success")
else:
    print("Search string not found")
