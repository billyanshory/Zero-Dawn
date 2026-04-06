import re

filepath = "sekolah-luar-biasa-55 ( idcloudhost - Layer of Quality Cyber Security - Third Effort ).py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Add cached_render function definition after the cache initialization
cached_render_code = """
from flask import current_app

def cached_render(template_name, template_string, **context):
    env = current_app.jinja_env
    if env.cache is not None:
        template = env.cache.get(template_name)
        if template is None:
            template = env.from_string(template_string)
            env.cache[template_name] = template
    else:
        template = env.from_string(template_string)
    return template.render(**context)
"""

if "def cached_render(" not in content:
    content = content.replace("app.config['WTF_CSRF_TIME_LIMIT'] = 3600", "app.config['WTF_CSRF_TIME_LIMIT'] = 3600\n" + cached_render_code)

# Replace all occurrences of render_template_string(HOME_HTML, ...)
# Because render_template_string is imported from flask and has the signature render_template_string(source, **context)
# we can safely replace it with cached_render('name', source, **context).
# But since we don't have the template name, we can use the variable name like 'HOME_HTML'.

# Find all occurrences of render_template_string(X, ...)
# X can be a string literal or variable, even compound like STYLES_HTML + RAMADHAN_STYLES...
# Better way: replace the call itself.
# We'll use a regex.

# We need to replace import
content = content.replace("from flask import Flask, request, send_from_directory, render_template_string, redirect, url_for, Response, jsonify, session",
                          "from flask import Flask, request, send_from_directory, redirect, url_for, Response, jsonify, session, render_template_string")

# Wait, instead of complicated regex, I can redefine render_template_string globally to do caching!
# In the file, import render_template_string as _render_template_string, then define our own render_template_string
# However, to be safe, it's better to explicitly replace them.

replace_def_render = """
import hashlib

def cached_render(template_string, **context):
    env = current_app.jinja_env
    if env.cache is not None:
        # Use a hash of the template string as the cache key since variable names aren't available
        # But hashing is slow? Jinja2 does parsing. Hash is fast.
        # Even better, use the id(template_string) or just a short hash.
        # Actually hash of 200KB is very fast.
        key = hashlib.md5(template_string.encode('utf-8')).hexdigest()
        template = env.cache.get(key)
        if template is None:
            template = env.from_string(template_string)
            env.cache[key] = template
    else:
        template = env.from_string(template_string)
    return template.render(**context)

# Override render_template_string in this module
render_template_string = cached_render
"""

if "def cached_render(" not in content:
    content = content.replace("from flask_caching import Cache\n", "from flask_caching import Cache\n" + replace_def_render)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("BUG-003 Patched via monkey-patching render_template_string.")
