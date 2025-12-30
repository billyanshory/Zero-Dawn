import unittest
import os
from mysite.flask_app import app, db, FamilyCardData, ADMIN_PASS_HASH
from werkzeug.security import check_password_hash

class BasicTests(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False # Disable CSRF for testing
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app.test_client()
        with app.app_context():
            db.create_all()

    def test_index_page(self):
        response = self.app.get('/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Selamat Datang', response.data)

    def test_password_hash(self):
        self.assertTrue(check_password_hash(ADMIN_PASS_HASH, 'NKRIhargamati'))
        self.assertFalse(check_password_hash(ADMIN_PASS_HASH, 'wrongpassword'))

    def test_database_insert(self):
        with app.app_context():
            new_data = FamilyCardData(nomor_kk="123", kepala_keluarga="Budi", alamat="Jalan A")
            db.session.add(new_data)
            db.session.commit()

            data = FamilyCardData.query.first()
            self.assertEqual(data.kepala_keluarga, "Budi")

if __name__ == "__main__":
    unittest.main()
