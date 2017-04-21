# -*- coding:utf-8 -*-
from casserver.authenticator import Authenticator


class DummyAuthenticator(Authenticator):

    def check_credentials(self, username, password, service=None):
        return not username is None and len(username.strip()) > 0 and username == password
