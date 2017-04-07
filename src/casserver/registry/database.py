from casserver.registry import *
import random
import string
from datetime import timedelta
import sqlite3

sqlite_ddl_script = """

    create table login_ticket(
        key varchar(35) not null
    );
    
    create table ticket_granting_ticket (
        key varchar(35) not null,
        username varchar(1024) not null
    );

    create table service_ticket(
        key varchar(35) not null,
        service varchar(1024) not null,
        tgt varchar(35) not null
    );
    
    create table proxy_granting_ticket(
        key varchar(36) not null,
        st varchar(35) not null,
        url varchar(1024) not null
    );

    create table proxy_ticket(
        key varchar(35) not null,
        pgt varchar(36) not null,
        target varchar(1024) not null
    );

"""

class DbTicketRegistry(TicketRegistry):
    class _Ticket:
        def __init__(ttype, key, username, iou=None):
            self.ttype=ttype
            self.key = key
            self.username = username
            self.iou = iou
        
        def __str__(self):
            return self.key
        
    def __init__(self, dbapi_module, connectionstring, loginTicketTtl=timedelta(minutes=5)):
        TicketRegistry.__init__(self, loginTicketTtl)
        self.conn = dbapi_module.connect(connectionstring)
    
    def db(self):
        return self.conn
            
    def new_login_ticket(self):
        lt = 'lt-' + (''.join(random.choice(string.ascii_lowercase+string.digits) for _ in range(32)))
        db = self.db()
        db.execute("insert into login_ticket(key) values(?)", [lt])
        db.commit()
        return LoginTicket(lt)

    def validate_login_ticket(self, lt):
        c = self.db().cursor()
        c.execute("select count(*) from login_ticket where key=?", [lt])
        return c.fetchone() > 0
        
    def new_service_ticket(self, service, username, tgt):
        st = 'st-' + (''.join(random.choice(string.ascii_lowercase+string.digits) for _ in range(32)))
        db = self.db()
        db.execute("insert into service_ticket(key, username, service, tgt) values(?,?,?,?)", [st, username, service, tgt])
        db.commit()
        return st
    
    def get_username_for_service_ticket(self, st):
        c = self.db().cursor()
        c.execute("select tgt.username from service_ticket st join ticket_granting_ticket tgt on st.tgt=tgt.key where st.key=?", [st])
        r = c.fetchall()
        return r[0] if r else None

    def get_service_ticket(self, service, st):
        c = self.db().cursor()
        c.execute("select key, username, service, tgt from service_ticket where key=? and service=?", [st, service])
        r = c.fetchall()
        return ServiceTicket(r[0], r[1], r[2]) if r else None
        return c.fetchone() > 0
    
    def new_ticket_granting_ticket(self, username):
        tgt = 'tgt-' + (''.join(random.choice(string.ascii_lowercase+string.digits) for _ in range(32)))
        db = self.db()
        db.execute("insert into ticket_granting_ticket(key, username) values(?,?)", [tgt, username])
        db.commit()
        return TicketGrantingTicket(tgt, username)
        
    def get_ticket_granting_ticket(self, tgt):
        c = self.db().cursor()
        c.execute("select username from ticket_granting_ticket where key=?", [tgt])
        r = c.fetchall()
        return TicketGrantingTicket(tgt, r[0][0]) if r else None

    def validate_ticket_granting_ticket(self, tgt):
        c = self.db().cursor()
        c.execute("select count(*) from ticket_granting_ticket where key=?", [tgt])
        return c.fetchone() > 0

    def delete_ticket_granting_ticket(self, tgt):
        c = self.db().cursor()
        c.execute("delete from ticket_granting_ticket where key=?", [tgt])
        pass
        
    def delete_proxy_granting_tickets_for_username(self, username):
        db = self.db()
        c = db.cursor()
        c.execute("select key from ticket_granting_ticket where username=?", [username])
        sts = []
        for tgt in c.fetchall():
            c.execute("select key from service_ticket where tgt=?", [tgt])
            sts += c.fetchall()
            db.execute("delete from service_ticket where tgt=?", [tgt])
        pgts = []
        for st in sts:
            c.execute("select key from service_ticket where st=?", [st])
            pgts += c.fetchall()
            db.execute("delete from proxy_granting_ticket where st=?", [st])
        for pgt in pgts:
            db.execute("delete from proxy_ticket where pgt=?", [tgt])
        db.commit()

    def new_proxy_granting_ticket(self, st, url):
        pgt = 'pgt-' + (''.join(random.choice(string.ascii_lowercase+string.digits) for _ in range(32)))
	db = self.db()
	db.execute("insert into proxy_granting_ticket(key, st,url) values(?,?,?)", [pgt, st, url])
	db.commit()
        return pgt

    def new_proxy_ticket(self, pgt, target):
        db = self.db()
        c = db.cursor()
	db = self.db()
        pt = 'pt-' + (''.join(random.choice(string.ascii_lowercase+string.digits) for _ in range(32)))
	db.execute("insert into proxy_ticket(key, pgt, target) values(?,?,?)", [pt, pgt, target])
	db.commit()
        return pt
    
    def validate_proxy_ticket(self, service, pt):
        db = self.db()
        c = db.cursor()
        c.execute("select count(*) from proxy_ticket where pt=?", [pt])
        return c.fetchone() == 1

