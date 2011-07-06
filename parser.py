#!/usr/bin/env python
# coding:utf-8

import sys, os, re, time
import logging
import marshal, zlib
import socket, httplib, urllib2, urlparse
import thread, threading
import redis
import urlparse
import lxml.etree
import profile

logging.basicConfig(level=logging.INFO, format='%(levelname)s - - %(asctime)s %(message)s', datefmt='[%d/%b/%Y %H:%M:%S]')

class Parser(threading.Thread):

    RDB_DOWNLOAD    = 'download'
    RDB_DOWNLOADING = 'downloading'
    RDB_DOWNLOADED  = 'downloaded'
    RDB_SAVE        = 'save'
    RDB_SAVEAS      = 'saveas'

    def __init__(self):
        threading.Thread.__init__(self)
        self.rdb = redis.Redis()
        self.setName('Parser '+ self.getName())

    def run(self):
        while 1:
            item = self.rdb.lpop(self.RDB_DOWNLOADED)
            if item is None:
                sleep = 0.01
                #logging.info('%r get None, sleep %s', self.getName(), sleep)
                time.sleep(sleep)
                continue
            try:
                info = marshal.loads(item)
                urltype, url, headers, content = info['urltype'], info['url'], info['headers'], info['content']
                logging.info('begin parse url=%r', url)
                links, save, saveas = profile.parse(urltype, url, headers, content)
                for link in links:
                    logging.info('parse out link: %r', link)
                    self.rdb.lpush(self.RDB_DOWNLOAD, link)
                if save:
                    value = marshal.dumps({'urltype': urltype, 'url':url, 'headers':headers, 'content':save})
                    self.rdb.lpush(self.RDB_SAVE, value)
                for link in saveas:
                    logging.info('parse out saveas link: %r', link)
                    self.rdb.lpush(self.RDB_SAVEAS, link)
                logging.info('end parse url=%r', url)
            except Exception, e:
                logging.exception('Error: %s', e)

def main():
    parser = Parser()
    parser.start()
    parser.join()

if __name__ == '__main__':
    main()

