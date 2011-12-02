#!/usr/bin/env python
# coding:utf-8

import sys, os, re, time
import logging
import urlparse

__plugins_map = {}

def __init__():
    plugins = set([os.path.splitext(x)[0] for x in os.listdir(os.path.dirname(__file__)) if not x.startswith('_') and x.endswith('.py')])
    sys.path.insert(0, os.path.dirname(__file__))
    for plugin in plugins:
        if plugin in __plugins_map:
            continue
        logging.info('try import plugins %r', plugin)
        mod = __import__(plugin)
        if not getattr(mod, '__domain__', None):
            logging.error('%s.__domain__ is None!', plugin)
            continue
        for interface in ('parse', 'save'):
            if not callable(getattr(mod, interface, None)):
                logging.critical('%s.%s is not callable!', plugin, interface)
                sys.exit(-1)
        logging.info('import plugins %r ok, domain=%r', plugin, mod.__domain__)
        for domain in mod.__domain__:
            __plugins_map[domain] = {'parse':mod.parse, 'save':mod.save}
    sys.path.pop(0)

def plugins_parse(info):
    netloc = urlparse.urlparse(info['url']).netloc
    return __plugins_map.get(netloc)['parse'](info)

def plugins_save(info):
    netloc = urlparse.urlparse(info['url']).netloc
    return __plugins_map.get(netloc)['save'](info)


__init__()




