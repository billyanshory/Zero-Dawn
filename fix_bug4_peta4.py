import re

with open("masjid-al-hijrah-63 ( idcloudhost - others 5 fitur - Idul Adha Qurban ).py", "r") as f:
    content = f.read()

# Verify that there are no unescaped {} in the HTML literals that will be passed to render_template_string
for view_name in [
    "IDUL_ADHA_DASHBOARD_HTML",
    "IDUL_ADHA_LAPORAN_HTML",
    "IDUL_ADHA_HEWAN_ADMIN_HTML",
    "IDUL_ADHA_LACAK_HTML",
    "IDUL_ADHA_PEMBAGIAN_CEK_HTML",
    "IDUL_ADHA_PEMBAGIAN_ADMIN_HTML",
    "IDUL_ADHA_PETA_DISTRIBUSI_HTML",
    "IDUL_ADHA_PANDUAN_HTML"
]:
    start = content.find(f"{view_name} = '''")
    if start != -1:
        end = content.find("'''", start + len(f"{view_name} = '''"))
        html = content[start:end]
        scripts = re.findall(r"<script>(.*?)</script>", html, re.DOTALL)
        for s in scripts:
            # Check if there are any unescaped { or }
            # Wait, double {{ will match single { if we regex but wait, jinja parses {{ as variable/expression so it evaluates it.
            # No, if it's Jinja `render_template_string`, then `{` and `}` themselves don't throw KeyError, `{{ }}` evaluates as Jinja expressions!
            # Wait, the prompt says "every time you write a JavaScript block embedded inside a Python string that uses f-string formatting, you must audit every single curly brace in that JavaScript block."
            # Are these strings f-strings?
            # They are declared as `IDUL_ADHA_LAPORAN_HTML = '''...'''` - these are NOT f-strings!
            # However, `render_template_string` will parse it as Jinja. In Jinja, `{` and `}` do not need escaping unless they are `{{` or `{%`.
            # BUT wait, the prompt specifically says "Python string formatting conflict where curly braces {} inside the JavaScript conflict with Python's .format() method or f-string interpolation... The fix is to either escape all JavaScript curly braces as {{ and }}, or to switch from f-string to .format() only for the Python-specific parts and keep the JavaScript blocks as raw string segments joined with concatenation."
            pass
