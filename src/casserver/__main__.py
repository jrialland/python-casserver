#!/usr/bin/env python2
# -*- coding: utf-8 -*-
if __name__ == '__main__':
    from casserver import create_app
    import sys, os, argparse, logging
    from bottle import run

    p = argparse.ArgumentParser()
    p.add_argument('--host', default='127.0.0.1', help='http bind address')
    p.add_argument('--port', default='8000', help='http server port')
    p.add_argument('--assets', default=os.path.dirname(__file__)+'/../../assets', help="location of static files")
    p.add_argument('--path', default='/cas', help='root path')
    p.add_argument('--debug', dest='debug', action='store_const', default=False, const=True, help='debug mode')
    args = p.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    path = args.path
    path = path if path  and path[0]=='/' else '/'+path

    logging.debug('Using path  :' + path)

    app = create_app(path, rootdir = args.assets)
    run(app=app, host=args.host, port=int(args.port), debug=args.debug, reloader=True)

