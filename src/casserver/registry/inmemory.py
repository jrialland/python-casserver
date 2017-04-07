from casserver.registry.database import DbTicketRegistry, sqlite_ddl_script
from datetime import timedelta
import logging
import sqlite3

class InMemoryTicketRegistry(DbTicketRegistry):
    def __init__(self, loginTicketTtl=timedelta(minutes=5)):
        DbTicketRegistry.__init__(self, sqlite3, ':memory:',loginTicketTtl=loginTicketTtl)
        for command in map(str.strip, sqlite_ddl_script.split(';')):
            logging.debug(command)
            self.db().execute(command)

