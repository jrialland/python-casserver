# -*- coding:utf-8 -*-
import unittest
import doctest
import sys
import os
import re
from webtest import TestApp
import casserver


class BaseTests(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(BaseTests, self).__init__(*args, **kwargs)
        assets = os.path.abspath(os.path.dirname(__file__) + '/../../assets')
        self.assertTrue(os.path.isdir(assets))
        self.app = TestApp(casserver.create_app('/cas', rootdir=assets))

    def test_static(self):
        r = self.app.get('/cas/static/screen.css')
        self.assertEqual('200 OK', r.status)

    def test_get_login(self):
        response = self.app.get('/cas/login')
        self.assertEqual('200 OK', response.status)
        self.assertTrue('input type="hidden" name="lt"' in response.body)

    def test_obtain_lt_get(self):
        self.app.get('/cas/loginTicket', status=405)

    def test_obtain_lt(self):
        response = self.app.post('/cas/loginTicket')
        ticket = response.body
        self.assertTrue(ticket.startswith('lt-'))

    def test_login_missing_lt(self):
        form = self.app.get('/cas/login').form
        form['username'] = 'test'
        form['password'] = 'test'
        form['lt'] = ''
        response = form.submit(status=200)

    def test_login_wrong_password(self):
        form = self.app.get('/cas/login').form
        form['username'] = 'test'
        form['password'] = 'invalid'
        response = form.submit(status=401)

    def test_login_ok(self):
        form = self.app.get('/cas/login').form
        form['username'] = 'test'
        form['password'] = 'test'
        response = form.submit(status=200)
        self.assertTrue('Set-Cookie' in response.headers)
        self.assertTrue(
            re.match('^tgt=tgt-.+', response.headers['Set-Cookie']))

    def test_login_redirect_to_service(self):
        form = self.app.get('/cas/login', params={
                            'service': 'http://mydomain.test'}).form
        form['username'] = 'test'
        form['password'] = 'test'
        response = form.submit(status=303)
        self.assertTrue('Set-Cookie' in response.headers)
        self.assertTrue(
            re.match('^tgt=tgt-.+', response.headers['Set-Cookie']))
        self.assertTrue(
            response.headers['Location'].startswith('http://mydomain.test'))
