fname = "sekolah-luar-biasa-83 ( idcloudhost - pengembalian kembali - dashboard guru).py"
with open(fname, 'r') as f:
    content = f.read()

# Clean up flash, current_app duplicates
content = content.replace("from flask import Flask, request, send_from_directory, redirect, url_for, Response, jsonify, session, render_template_string, flash, current_app, flash, current_app, flash, current_app", "from flask import Flask, request, send_from_directory, redirect, url_for, Response, jsonify, session, render_template_string, flash, current_app")

with open(fname, 'w') as f:
    f.write(content)
