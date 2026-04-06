filepath = "sekolah-luar-biasa-55 ( idcloudhost - Layer of Quality Cyber Security - Third Effort ).py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Make sure we actually add the function since the previous script might have failed the if check due to newline difference

replace_def_render = """from flask_caching import Cache

import hashlib
from flask import current_app

def cached_render(template_string, **context):
    env = current_app.jinja_env
    if env.cache is not None:
        key = hashlib.md5(template_string.encode('utf-8')).hexdigest()
        template = env.cache.get(key)
        if template is None:
            template = env.from_string(template_string)
            env.cache[key] = template
    else:
        template = env.from_string(template_string)
    return template.render(**context)

render_template_string = cached_render
"""

if "def cached_render" not in content:
    content = content.replace("from flask_caching import Cache", replace_def_render)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Patched.")
else:
    print("Already patched.")
