# -*- coding:utf-8 -*-

import os
import re
import logging
from collections import defaultdict
from bottle import Bottle, request, response, redirect, abort, static_file

from .authenticator.dummy import DummyAuthenticator
from .registry.inmemory import InMemoryTicketRegistry
from .util import *


class TemplateRenderer:

    def __init__(self, tpldir='./resources', defaultparams={}):
        from bottle import SimpleTemplate
        import fnmatch
        self.defaultparams = defaultparams
        self.templates = {}
        for root, dirnames, filenames in os.walk(tpldir):
            for filename in fnmatch.filter(filenames, '*.stpl'):
                if filename[0] <> '_':
                    tplname = re.sub('\\.stpl$', '', filename)
                    logging.info(
                        "loading template '{0}' from '{1}'".format(tplname, filename))
                    with file(os.path.join(root, filename), 'r') as stpl:
                        self.templates[tplname] = SimpleTemplate(stpl.read())

    def render(self, tplname, **kwargs):
        return self.templates[tplname].render(**dict(kwargs.items() + self.defaultparams.items()))


def create_app(uri_path='', rootdir=os.path.dirname(__file__), ticketRegistry=InMemoryTicketRegistry(), authenticator=DummyAuthenticator()):
    """
    Create a Bottle application.
    """
    app = Bottle()
    templateRenderer = TemplateRenderer(os.path.join(rootdir, 'views'))

    def get_request_params(*args):
        values = []
        for p in args:
            if p in request.params and request.params[p] != 'None':
                values.append(request.params[p])
            else:
                values.append(None)
        return values

    @app.route(uri_path + '/static/<filename:path>')
    def static(filename):
        r = os.path.abspath(os.path.join(rootdir, 'static', filename))
        return static_file(os.path.basename(filename), root=os.path.dirname(r))

    @app.route(uri_path + '<:re:/?>')
    def redirect_to_login():
        redirect(uri_path + '/login')

    @app.get(uri_path + '/login')
    def credentials_requestor():
        # make sure there's no caching
        response.set_header('Pragma', 'no-cache')
        response.set_header('Cache-Control', 'no-store')
        response.set_header('Pragma', 'no-cache')
        response.set_header(
            'Expires', to_rfc2822(datetime.now() - timedelta(days=365)))
        service, renew, gateway = get_request_params(
            'service', 'renew', 'gateway')
        gateway = gateway in ['1', 'true']
        tgt = ticketRegistry.get_ticket_granting_ticket(
            request.get_cookie('tgc'))
        if service:
            if renew:
                logging.info(
                    'Authentication renew explicitly requested. Proceeding with CAS login for service ' + service)
            elif tgt:
                logging.info("Valid ticket granting ticket detected.")
                serviceTicket = ticketRegistry.new_service_ticket(
                    service, tgt.username, tgt)
                service_url_with_ticket = make_url_with_extraparam(
                    service, 'st', serviceTicket.st)
                logging.info(
                    "User '" + tgt.username + "' authenticated based on ticket granting cookie. Redirecting to " + service_url_with_ticket)
                redirect(303, service_url_with_ticket)
                         # response code 303 means "See Other" (see Appendix B
                         # in CAS Protocol spec)
                return
            elif gateway:
                logging.info(
                    "Redirecting unauthenticated gateway request to service " + service)
                redirect(303, service)
                return
        elif gateway:
            logging.warn(
                "This is a gateway request but no service parameter was given!")
        else:
            logging.info("Proceeding with CAS login without a target service.")
        return templateRenderer.render('loginform', lt=ticketRegistry.new_login_ticket().lt, service=service)

    @app.post(uri_path + '/login')
    def credentials_acceptor():
        username, password, service, lt = get_request_params(
            'username', 'password', 'service', 'lt')
        username = username.strip() if username else ''
        if not ticketRegistry.validate_login_ticket(lt):
            logging.info('Missing or invalid login ticket')
            response.status = 500
            return templateRenderer.render('loginform', lt=ticketRegistry.new_login_ticket())
        else:
            valid = False
            try:
                valid = authenticator.check_credentials(
                    username, password, service)
            except Exception as e:
                logging.exception('authenticator failure')
            if valid:
                logging.info(
                    "Credentials for username '{0}' successfully validated".format(username))
                ticketGrantingTicket = ticketRegistry.new_ticket_granting_ticket(
                    username)
                logging.debug('tgt : ' + repr(ticketGrantingTicket.tgt))
                response.set_cookie('tgt', ticketGrantingTicket.tgt)
                logging.info("Ticket granting cookie '{0}' granted to user '{1}'".format(
                    ticketGrantingTicket.tgt, username))
                if service:
                    serviceTicket = ticketRegistry.new_service_ticket(
                        service, username, ticketGrantingTicket.tgt)
                    service_with_ticket = make_url_with_extraparam(
                        service, 'st', serviceTicket.st)
                    logging.info('Redirecting to ' + service_with_ticket)
                    redirect(service_with_ticket, code=303)
                else:
                    logging.info('No service parameter was provided')
                    return templateRenderer.render('auth_success', username=username)
            else:
                logging.info(
                    "Invalid credentials for username '{0}'".format(username))
                response.status = 401
                return templateRenderer.render('loginform', lt=ticketRegistry.new_login_ticket().lt, username=username, error_message='Invalid credentials')

    @app.route(uri_path + '/logout')
    def logout():
        service, destination, continue_url, gateway = get_request_params(
            'service', 'destination', 'url', 'gateway')
        service = destination if service is None else service
        gateway = gateway in ['1', 'true']
        tgt = request.get_cookie("tgt")
        response.set_cookie('tgt', '', expires=0)
        ticketGrantingTicket = ticketRegistry.get_ticket_granting_ticket(tgt)
        if ticketGrantingTicket:
            ticketRegistry.delete_ticket_granting_ticket(
                ticketGrantingTicket.tgt)
            username = ticketGrantingTicket.username
            if username:
                ticketRegistry.delete_proxy_granting_tickets_for_username(
                    username)
                logging.info("User '{0}' logged out".format(username))

        if gateway and service:
            logging.info('Redirecting to ' + service)
            redirect(303, service)
        elif continue_url:
            templateRender.render('logout', continue_url=continue_url)
        else:
            return templateRenderer.render('loginform', lt=ticketRegistry.new_login_ticket(), message='You have been successfully logged out', service=service)

    @app.get(uri_path + '/loginTicket')
    def loginTicket_needs_post():
        abort(405, 'This URI only accepts POST requests')

    @app.post(uri_path + '/loginTicket')
    def loginTicket():
        response.set_header('Content-Type', 'text/plain')
        return ticketRegistry.new_login_ticket().lt

    @app.get(uri_path + '/validate')
    def validate():
        service, ticket, renew = get_request_params(
            'service', 'ticket', 'renew')
        renew = renew in ['1', 'true']
        serviceTicket = ticketRegistry.get_service_ticket(service, ticket)
        response.set_header('Content-Type', 'text/plain')
        if serviceTicket:
            return 'yes\n#' + serviceTicket.username + '\n'
        else:
            return 'no\n\n'

    def tkValidate(isproxy):
        service, ticket, pgt_url, renew = get_request_params(
            'service', 'ticket', 'pgtUrl', 'renew')
        renew = renew in ['1', 'true']
        dic = defaultdict(lambda: None)

        valid
        username
        dic['service'] = service
        dic['ticket'] = ticket
        dic['pgt_url'] = pgt_url
        dic['renew'] = renew
        dic['proxies'] = []

        valid = False
        if isproxy:
            valid = ticketRegistry.validate_proxy_ticket(service, ticket)
        else:
            valid = not ticketRegistry.get_service_ticket(
                service, ticket) is None
        dic['valid'] = valid

        if valid:
            if pgt_url:
                pgt = ticketRegistry.new_proxy_granting_ticket(ticket, pgt_url)
                if pgt:
                    dic['pgt'] = pgt
                    dic['pgtiou'] = pgt.iou

        response.set_header('Content-Type', 'text/xml;Charset=utf-8')
        return templateRenderer.render('proxy_validate', service=service, )

    @app.get(uri_path + '/serviceValidate')
    def serviceValidate():
        return tkValidate(isproxy=False)

    @app.get(uri_path + '/proxyValidate')
    def proxyValidate():
        return tkValidate(isProxy=True)

    @app.get(uri_path + '/proxy')
    def proxy():
        pgt, target_service = get_request_params('pgt', 'targetService')
        valid = ticketRegistry.validate_proxy_granting_ticket(pgt)
        pt = ticketRegistry.new_proxy_ticket(
            pgt, target_service) if valid else None
        return templateRenderer.render('proxy', pt=pt, valid=valid)
    return app
