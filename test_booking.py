# Ah, SESSION_COOKIE_SECURE is True, which means the browser (or requests.Session)
# won't send the cookie back over HTTP (like http://127.0.0.1:5000).
# I'll just change the URL to https or mock the session or disable SECURE for the test.

import requests
import sqlite3

session = requests.Session()
# To bypass, we can either configure the test properly or just do a unit test using Flask's test_client.
