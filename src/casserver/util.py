
from urllib import urlencode
from urlparse import parse_qs, urlsplit, urlunsplit

import time
from datetime import datetime, timedelta
import email.utils



def to_rfc2822(dt=datetime.now()):
    tstamp = time.mktime(dt.timetuple())
    return email.utils.formatdate(tstamp) 



def make_url_with_extraparam(url, k, v):
    scheme, netloc, path, query_string, fragment = urlsplit(url)
    query_params = parse_qs(query_string)
    query_params[k] = [v]
    new_query_string = urlencode(query_params, doseq=True)
    return urlunsplit((scheme, netloc, path, new_query_string, fragment))



