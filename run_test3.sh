sed -i "s/app.config\['SQLALCHEMY_ENGINE_OPTIONS'\]/#app.config\['SQLALCHEMY_ENGINE_OPTIONS'\]/" app.py
python test_endpoints.py
