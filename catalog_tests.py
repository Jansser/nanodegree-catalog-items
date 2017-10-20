import flask
from flask import url_for
from app import app
import os
import unittest
import tempfile


class FlaskTestCase(unittest.TestCase):
    def setUp(self):
        app.secret_key = 'slimShady'
        app.config['SERVER_NAME'] = 'localhost'

        self.app = app.test_client()
        self.app.testing = True

    def tearDown(self):
        pass

    def test_home_status_code(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)

    def test_redirect_new_item_not_authorized(self):
        response = self.app.get('/catalog/new')
        assert '/login' in response.location

    def test_redirect_edit_item_not_authorized(self):
        with app.app_context():
            response = self.app.get(url_for('edit_item',
                                            category_name='soccer',
                                            item_name='Jersey'))
            assert '/login' in response.location

    def test_redirect_delete_item_not_authorized(self):
        with app.app_context():
            response = self.app.get(url_for('delete_item',
                                            category_name='soccer',
                                            item_name='Jersey'))
            assert '/login' in response.location


if __name__ == '__main__':
    unittest.main()
