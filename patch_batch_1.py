import re

with open("app.py", "r") as f:
    content = f.read()

# Replace `content = f"""` block
def replace_fstring(match):
    text = match.group(1)
    # Replace single braces with double braces for variables
    text = text.replace('{acc_no}', '{{ acc_no }}')
    text = text.replace('{qris_url}', '{{ qris_url }}')
    text = text.replace('{bg_class}', '{{ bg_class }}')
    text = text.replace('{card_class}', '{{ card_class }}')
    text = text.replace('{text_highlight}', '{{ text_highlight }}')

    # Replace double braces for tags with single braces
    text = text.replace('{{% if is_admin %}}', '{% if is_admin %}')
    text = text.replace('{{% endif %}}', '{% endif %}')

    # Replace JavaScript double brace block
    text = text.replace("{{ if(typeof formatBankDisplay === 'function') formatBankDisplay('donate-rek-text'); }}", "{ if(typeof formatBankDisplay === 'function') formatBankDisplay('donate-rek-text'); }")

    return 'content = """' + text + '"""'

content = re.sub(r'content\s*=\s*f"""(.*?)"""', replace_fstring, content, flags=re.DOTALL)

# Update render_template_string calls
search_render = r"return render_template_string\(BASE_LAYOUT,\s*styles=STYLES_HTML \+ \(RAMADHAN_STYLES if source=='ramadhan' else \(IRMA_STYLES if source=='irma' else ''\)\),\s*active_page='donate',\s*theme=theme,\s*content=render_template_string\(content,\s*is_admin=is_admin,\s*settings=get_settings\(\)\),\s*is_admin=is_admin\)"
replace_render = "return render_template_string(BASE_LAYOUT, styles=STYLES_HTML + (RAMADHAN_STYLES if source=='ramadhan' else (IRMA_STYLES if source=='irma' else '')), active_page='donate', theme=theme, content=render_template_string(content, is_admin=is_admin, settings=get_settings(), acc_no=acc_no, qris_url=qris_url, bg_class=bg_class, card_class=card_class, text_highlight=text_highlight), is_admin=is_admin, settings=get_settings())"

content = re.sub(search_render, replace_render, content)

with open("app.py", "w") as f:
    f.write(content)

print("Patch 1 applied.")
