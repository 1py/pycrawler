#!/usr/bin/env python
# coding:utf-8

import sys, os, re, time
import logging
import json, zlib

__plugins_map = {}

def __init__():
    plugins = set([os.path.splitext(x)[0] for x in os.listdir(os.path.dirname(__file__)) if not x.startswith('_') and x.endswith('.py')])
    sys.path.insert(0, os.path.dirname(__file__))
    for plugin in plugins:
        if plugin in __plugins_map:
            continue
        logging.info('try import plugins %r', plugin)
        mod = __import__(plugin)
        for interface in ('encoding', 'parse', 'save'):
            if not callable(getattr(mod, interface, None)):
                logging.critical('%s.%s is not callable!', plugin, interface)
                sys.exit(-1)
        __plugins_map[plugin] = {'encoding':mod.encoding, 'parse':mod.parse, 'save':mod.save}
    sys.path.pop(0)

def plugins_encoding(info):
    return __plugins_map.get(info['tag'])['encoding'](info)

def plugins_parse(info):
    return __plugins_map.get(info['tag'])['parse'](info)

def plugins_save(info):
    return __plugins_map.get(info['tag'])['save'](info)


__init__()




