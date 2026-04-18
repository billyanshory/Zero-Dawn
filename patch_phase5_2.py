with open("app.py", "r") as f:
    content = f.read()

old_emoji = """def prefetch_emoji_icons() -> None:
    def _download():
        try:
            emoji_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'emoji_cache')
            os.makedirs(emoji_dir, exist_ok=True)
            hex_codes = ['1f441', '1f442', '1f3c3', '1f590', '1f3af', '1f5e3', '2753']
            for icon_hex in hex_codes:
                file_path = os.path.join(emoji_dir, f"{icon_hex}.png")
                if not os.path.exists(file_path):
                    url = f"https://cdnjs.cloudflare.com/ajax/libs/twemoji/14.0.2/72x72/{icon_hex}.png"
                    try:
                        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
                        if response.status_code == 200:
                            with open(file_path, 'wb') as out_f:
                                out_f.write(response.content)
                    except Exception as e:
                        app.logger.error(f"Failed to prefetch emoji {icon_hex}", exc_info=True)
        except Exception as e:
            app.logger.error("Background thread error in prefetch_emoji_icons", exc_info=True)

    threading.Thread(target=_download, daemon=True).start()"""

new_emoji = """def prefetch_emoji_icons() -> None:
    def _download():
        try:
            emoji_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'emoji_cache')
            try:
                os.makedirs(emoji_dir, exist_ok=True)
            except OSError:
                app.logger.info("Emoji cache directory not writable; skipping prefetch.")
                return

            _redis_url = os.getenv('REDIS_URL')
            if _redis_url:
                r = redis.from_url(_redis_url, socket_timeout=2)
                if not r.set("slb_emoji_prefetch", "1", nx=True, ex=86400):
                    return

            hex_codes = ['1f441', '1f442', '1f3c3', '1f590', '1f3af', '1f5e3', '2753']
            for icon_hex in hex_codes:
                file_path = os.path.join(emoji_dir, f"{icon_hex}.png")
                if not os.path.exists(file_path):
                    url = f"https://cdnjs.cloudflare.com/ajax/libs/twemoji/14.0.2/72x72/{icon_hex}.png"
                    try:
                        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=(3, 10))
                        if response.status_code == 200:
                            with open(file_path, 'wb') as out_f:
                                out_f.write(response.content)
                    except requests.RequestException:
                        app.logger.warning(f"Failed to prefetch emoji {icon_hex}", exc_info=True)
        except Exception:
            app.logger.error("Background thread error in prefetch_emoji_icons", exc_info=True)

    eventlet.spawn(_download)"""

content = content.replace(old_emoji, new_emoji)

with open("app.py", "w") as f:
    f.write(content)
