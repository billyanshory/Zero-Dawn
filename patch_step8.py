with open("sekolah-luar-biasa-90 ( idcloudhost - Nineteenth Layer of Quality Control - Data Privacy & Compliance (SLB-Specific) - v.89 - Opus 4.7 Ad. Think ).py", "r") as f:
    text = f.read()

search = """if os.getenv('SENTRY_DSN'):
    try:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
        sentry_sdk.init(
            dsn=os.getenv('SENTRY_DSN'),
            integrations=[FlaskIntegration()],
            traces_sample_rate=float(os.getenv('SENTRY_TRACES_RATE', 0.05))
        )
        app.logger.info("Sentry initialization successful.")
    except ImportError:
        app.logger.warning("SENTRY_DSN is set but sentry_sdk is not installed.")"""

replace = """try:
    if os.getenv('SENTRY_DSN'):
        _SENSITIVE_KEYS = frozenset([
            'nik', 'password', 'nama_lengkap', 'nama_panggilan', 'diagnosis_utama',
            'alergi_kritis', 'pemicu_tantrum', 'strategi_penenangan', 'kemampuan_komunikasi',
            'hotline_darurat_nama', 'hotline_darurat_nomor', 'kondisi_terkini', 'subscription_info', 'session'
        ])

        def _sentry_scrubber(event, hint):
            def _scrub(obj):
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        if isinstance(k, str) and k.lower() in _SENSITIVE_KEYS:
                            obj[k] = '[REDACTED]'
                        elif isinstance(v, (dict, list)):
                            _scrub(v)
                elif isinstance(obj, list):
                    for item in obj:
                        _scrub(item)

            if 'request' in event:
                _scrub(event['request'])
            if 'extra' in event:
                _scrub(event['extra'])
            if 'contexts' in event:
                _scrub(event['contexts'])
            return event

        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
        sentry_sdk.init(
            dsn=os.getenv('SENTRY_DSN'),
            integrations=[FlaskIntegration()],
            traces_sample_rate=float(os.getenv('SENTRY_TRACES_RATE', 0.05)),
            send_default_pii=False,
            before_send=_sentry_scrubber,
            before_breadcrumb=_sentry_scrubber
        )
        app.logger.info("Sentry initialization successful.")
except ImportError:
    app.logger.warning("SENTRY_DSN is set but sentry_sdk is not installed.")
except Exception:
    app.logger.error("Failed to initialize Sentry.", exc_info=True)"""

if search in text:
    text = text.replace(search, replace)
    with open("sekolah-luar-biasa-90 ( idcloudhost - Nineteenth Layer of Quality Control - Data Privacy & Compliance (SLB-Specific) - v.89 - Opus 4.7 Ad. Think ).py", "w") as f:
        f.write(text)
    print("Success")
else:
    print("Search string not found")
