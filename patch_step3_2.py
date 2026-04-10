with open('app.py', 'r') as f:
    content = f.read()

# Add a specific var for the mobile border
border_badge_old = """            <p class="text-[10px] font-bold {{ t_icon_text }} {{ t_icon_bg }} px-2 py-1 rounded-full border border-emerald-200" id="hijri-date">Loading...</p>"""
border_badge_new = """            {% set t_border_badge = 'border-rose-200' if theme and theme.icon_text == 'text-rose-600' else 'border-emerald-200' %}
            <p class="text-[10px] font-bold {{ t_icon_text }} {{ t_icon_bg }} px-2 py-1 rounded-full border {{ t_border_badge }}" id="hijri-date">Loading...</p>"""
content = content.replace(border_badge_old, border_badge_new)

with open('app.py', 'w') as f:
    f.write(content)
print("Done step 2.")
