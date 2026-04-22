import sys

try:
    # Just import it to see if it causes any immediate syntax or initialization crashes
    import importlib.util
    spec = importlib.util.spec_from_file_location("app_module", "masjid-al-hijrah-61 ( idcloudhost - tombol akses, page, & first fitur - Idul Adha Qurban ).py")
    app_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app_module)
    print("Module loaded successfully without crashes.")
except Exception as e:
    print(f"Error loading module: {e}")
    sys.exit(1)
