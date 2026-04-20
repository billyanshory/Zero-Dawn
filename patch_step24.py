with open("sekolah-luar-biasa-90 ( idcloudhost - Nineteenth Layer of Quality Control - Data Privacy & Compliance (SLB-Specific) - v.89 - Opus 4.7 Ad. Think ).py", "r") as f:
    text = f.read()

search = """    class _PIIScrubFilter(logging.Filter):
        def filter(self, record):
            msg = str(record.getMessage()).lower()
            for k in _SENSITIVE_LOG_KEYS:
                if k in msg:
                    record.msg = f"[MESSAGE REDACTED: contained sensitive key '{k}']"
                    record.args = ()
                    return True
            return True"""

replace = """    class _PIIScrubFilter(logging.Filter):
        def filter(self, record):
            msg_str = str(record.getMessage())
            try:
                msg_dict = _json_module.loads(msg_str)
                def _scrub_log(obj):
                    if isinstance(obj, dict):
                        for k, v in obj.items():
                            if isinstance(k, str) and k.lower() in _SENSITIVE_LOG_KEYS:
                                obj[k] = '[REDACTED]'
                            elif isinstance(v, (dict, list)):
                                _scrub_log(v)
                    elif isinstance(obj, list):
                        for item in obj:
                            _scrub_log(item)
                _scrub_log(msg_dict)
                record.msg = _json_module.dumps(msg_dict)
                record.args = ()
            except _json_module.JSONDecodeError:
                msg_lower = msg_str.lower()
                for k in _SENSITIVE_LOG_KEYS:
                    if k in msg_lower:
                        record.msg = f"[MESSAGE REDACTED: contained sensitive key '{k}']"
                        record.args = ()
                        break
            return True"""

if search in text:
    text = text.replace(search, replace)
    with open("sekolah-luar-biasa-90 ( idcloudhost - Nineteenth Layer of Quality Control - Data Privacy & Compliance (SLB-Specific) - v.89 - Opus 4.7 Ad. Think ).py", "w") as f:
        f.write(text)
    print("Success")
else:
    print("Search string not found")
