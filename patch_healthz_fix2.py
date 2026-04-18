with open("app.py", "r") as f:
    content = f.read()

content = content.replace("@app.after_request\n@app.after_request", "@app.after_request")

with open("app.py", "w") as f:
    f.write(content)
