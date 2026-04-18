with open("app.py", "r") as f:
    content = f.read()

init_pattern = r"db = SQLAlchemy\(app\)"
init_replacement = """db = SQLAlchemy(app)
migrate = Migrate(app, db, directory='migrations', compare_type=True)"""
content = content.replace("db = SQLAlchemy(app)\n", init_replacement + "\n")

with open("app.py", "w") as f:
    f.write(content)
