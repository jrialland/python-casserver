from casserver.authenticator import Authenticator

class DummyAuthenticator(Authenticator):
    def check_credentials(self, username, password, service=None):
        return username == password
