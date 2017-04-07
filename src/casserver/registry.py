from abc import ABCMeta, abstractmethod

class Ticket:
    pass

class LoginTicket(Ticket):
    __slots__ = ('lt')
    def __init__(self, lt):
        self.lt = lt

class TicketGrantingTicket(Ticket):
    __slots__ = ('tgt', 'username')
    def __init__(self, tgt, username):
        self.tgt = tgt
        self.username = username

class ServiceTicket(Ticket):
    __slots = ('st', 'username', 'service', 'tgt')
    def __init__(self, st, username, service, tgt=None):
        self.st = st
        self.username = username
        self.tgt = tgt

class TicketRegistry:
    __metaclass__ = ABCMeta
    __slots__ = ('loginTicketTtl')
    def __init__(self, loginTicketTtl):
        self.loginTicketTtl = loginTicketTtl
        
    @abstractmethod
    def new_login_ticket(self):
        """ generates a new LoginTicket and it in the persistent storage
            @return LoginTicket
        """
        raise NotImplementedError
    
    @abstractmethod
    def validate_login_ticket(self, lt):
        """ Verifies that the passed login ticket id is valid
            @return True or False
        """
        raise NotImplementedError
        
    @abstractmethod
    def new_ticket_granting_ticket(self, username):
        """ Create a new TicketGrantingTicket for an user.
            @Return a TicketGrantingTicket
        """
        raise NotImplementedError

    @abstractmethod
    def validate_ticket_granting_ticket(self, ticket):
        #shall return and object with a 'tgc' field and a 'username' field
        pass
    
    @abstractmethod
    def delete_ticket_granting_ticket(self, tgt):
        """ Deletes a Tgt. the argument is the tgt id.
            The method should also delete all associated service ticket if any
        """
        raise NotImplementedError

    @abstractmethod
    def new_service_ticket(self, service, username, tgt):
        """ Create an new ServiceTicket """
        raise NotImplementedError

    @abstractmethod
    def get_service_ticket(self, st):
        """ get a service ticket """
        raise NotImplementedError

    @abstractmethod
    def delete_proxy_granting_tickets_for_username(self, username):
        pass
    
    @abstractmethod
    def new_proxy_granting_ticket(self, st, username):
        pass #iou
    
    @abstractmethod
    def new_proxy_ticket(self, pgt, target):
        pass
    
    @abstractmethod
    def validate_proxy_ticket(self, service, pt):
        pass

