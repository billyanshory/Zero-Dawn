import os
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["LLM_API_KEY"] = "sk-test"
os.environ["LLM_MODEL_NAME"] = "gpt-4o"
os.environ["APP_SECRET"] = "test"
os.environ["SANIC_ENV"] = "development"
import app
app.app.run(host="127.0.0.1", port=8000, single_process=True)
