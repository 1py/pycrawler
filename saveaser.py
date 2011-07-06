#!/usr/bin/env python
# coding:utf-8

import sys, os, re, time
import logging
import marshal, zlib
import thread, threading
import redis
import profile
import urllib2
import socket

logging.basicConfig(level=logging.INFO, format='%(levelname)s - - %(asctime)s %(message)s', datefmt='[%d/%b/%Y %H:%M:%S]')

class SaveAser(threading.Thread):

    RDB_DOWNLOAD    = 'download'
    RDB_DOWNLOADING = 'downloading'
    RDB_DOWNLOADED  = 'downloaded'
    RDB_SAVE        = 'save'
    RDB_SAVEAS      = 'saveas'

    def __init__(self, *args, **kwargs):
        threading.Thread.__init__(self)
        self.rdb = redis.Redis(*args, **kwargs)
        self.opener = urllib2.build_opener()
        self.setName('Saver '+ self.getName())

    def run(self):
        while 1:
            item = self.rdb.lpop(self.RDB_SAVEAS)
            if item is None:
                sleep = 0.1
                #logging.info('%r get None, sleep %s', self.getName(), sleep)
                time.sleep(sleep)
                continue
            try:
                urltype, title, url = item.split()
                logging.info('begin saveas type=%r, title=%r, url=%r', urltype, title, url)
                for i in xrange(1, 4):
                    try:
                        logging.info('fetch url=%r, times=%d', url, i)
                        response = self.opener.open(url, timeout=20)
                        content = response.read()
                        break
                    except urllib2.URLError, e:
                        sleep = i*20
                        logging.exception('URLError: %s, sleep=%s', e, sleep)
                        time.sleep(sleep)
                    except socket.error, e:
                        sleep = i*20
                        logging.exception('socket.error: %s, sleep=%s', e, sleep)
                        time.sleep(sleep)
                else:
                    logging.error('fetch %r failed')
                    self.rdb.zrem(self.RDB_DOWNLOADING, url)
                    continue
                profile.saveas(urltype, url, response.headers.dict, content, title)
                logging.info('end saveas type=%r, title=%r, url=%r', urltype, title, url)
            except Exception, e:
                logging.exception('Error: %s', e)

def main():
    threadnumber = int(sys.argv[1])
    threads = []
    for i in xrange(threadnumber):
        t = SaveAser()
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

if __name__ == '__main__':
    main()

