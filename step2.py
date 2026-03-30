import re

with open("kampus-stie-samarinda-21 ( idcloudhost - Third Layer of Quality Control ).py", "r") as f:
    content = f.read()

# 1. Init Flask-Login
init_login = """
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'index'
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
"""
content = content.replace("app = Flask(__name__)", "app = Flask(__name__)\n" + init_login)

# 2. Update Model User
content = content.replace("class User(db.Model):", "class User(db.Model, UserMixin):")

# 3. Update Login Route
login_code = """
        login_user(user)
        session['user_id'] = user.id
        session['username'] = user.username
        session['npm'] = user.username
        session['nama'] = user.nama
        session['role'] = user.role
        session.permanent = True
"""
content = content.replace("""        session['user_id'] = user.id
        session['username'] = user.username
        session['npm'] = user.username
        session['nama'] = user.nama
        session['role'] = user.role
        session.permanent = True""", login_code)

# 4. Update Logout Route
logout_code = """
    logout_user()
    session.pop('is_admin', None)
    session.pop('is_gallery_admin', None)
"""
content = content.replace("""    session.pop('is_admin', None)
    session.pop('is_gallery_admin', None)""", logout_code)

with open("kampus-stie-samarinda-21 ( idcloudhost - Third Layer of Quality Control ).py", "w") as f:
    f.write(content)
