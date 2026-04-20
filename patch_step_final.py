with open("sekolah-luar-biasa-90 ( idcloudhost - Nineteenth Layer of Quality Control - Data Privacy & Compliance (SLB-Specific) - v.89 - Opus 4.7 Ad. Think ).py", "r") as f:
    text = f.read()

# Fix __file__ in prefetch_emoji_icons since we're in __main__
text = text.replace("emoji_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'emoji_cache')", "emoji_dir = os.path.join(os.path.abspath(os.path.dirname(__file__) if '__file__' in globals() else os.getcwd()), 'emoji_cache')")

with open("sekolah-luar-biasa-90 ( idcloudhost - Nineteenth Layer of Quality Control - Data Privacy & Compliance (SLB-Specific) - v.89 - Opus 4.7 Ad. Think ).py", "w") as f:
    f.write(text)
