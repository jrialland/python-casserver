from abc import ABCMeta, abstractmethod
    
class Authenticator:
    __metaclass__ = ABCMeta
    __slots__ = ()        
    @abstractmethod
    def check_credentials(self, username, password, service=None):
        raise NotImplementedError



