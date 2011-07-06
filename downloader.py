#!/usr/bin/env python
# coding:utf-8

import sys, os, re, time
import logging
import marshal
import socket, httplib, urllib2, urlparse
import thread, threading
import redis
import urlparse
import lxml.etree, zlib

logging.basicConfig(level=logging.INFO, format='%(levelname)s - - %(asctime)s %(message)s', datefmt='[%d/%b/%Y %H:%M:%S]')

class Downloader(threading.Thread):

    RDB_DOWNLOAD    = 'download'
    RDB_DOWNLOADING = 'downloading'
    RDB_DOWNLOADED  = 'downloaded'
    RDB_SAVE        = 'save'
    RDB_SAVEAS      = 'saveas'

    def __init__(self, *args, **kwargs):
        threading.Thread.__init__(self)
        self.rdb = redis.Redis(*args, **kwargs)
        self.opener = urllib2.build_opener()
        self.setName('Downloader '+ self.getName())

    def run(self):
        while 1:
            item = self.rdb.lpop(self.RDB_DOWNLOAD)
            if item is None:
                sleep = 0.01
                time.sleep(sleep)
                continue
            try:
                urltype, url = item.split()
                logging.info('%s fetch type=%r, url=%r', self.getName(), urltype, url)
                self.rdb.zadd(self.RDB_DOWNLOADING, url, 1)
                for i in xrange(1, 4):
                    try:
                        logging.info('fetch url=%r, times=%d', url, i)
                        response = self.opener.open(url, timeout=20)
                        content = response.read()
                        break
                    except urllib2.URLError, e:
                        logging.exception('URLError: %s', e)
                    except socket.error, e:
                        logging.exception('socket.error: %s', e)
                else:
                    logging.error('fetch %r failed')
                    self.rdb.zrem(self.RDB_DOWNLOADING, url)
                    continue
                self.rdb.zrem(self.RDB_DOWNLOADING, url)
                value = marshal.dumps({'urltype': urltype, 'url':url, 'headers':response.headers.dict, 'content':content})
                self.rdb.lpush(self.RDB_DOWNLOADED, value)
            except Exception, e:
                logging.exception('Exception Error: %s', e)

def init():
    rdb = redis.Redis()
    while 1:
        url = rdb.lpop(Downloader.RDB_DOWNLOADING)
        if url is None:
            break
        rdb.lpush(Downloader.RDB_DOWNLOAD)

def main():
    threadnumber = int(sys.argv[1])
    threads = []
    for i in xrange(threadnumber):
        t = Downloader()
        t.start()
        threads.append(t)
    for t in threads:
        t.join()


if __name__ == '__main__':
    main()

