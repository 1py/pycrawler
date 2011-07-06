#!/usr/bin/env python
# coding:utf-8

import sys, os, re, time
import logging
import marshal, zlib
import thread, threading
import redis
import profile

logging.basicConfig(level=logging.INFO, format='%(levelname)s - - %(asctime)s %(message)s', datefmt='[%d/%b/%Y %H:%M:%S]')

class Saver(threading.Thread):

    RDB_DOWNLOAD    = 'download'
    RDB_DOWNLOADING = 'downloading'
    RDB_DOWNLOADED  = 'downloaded'
    RDB_SAVE        = 'save'
    RDB_SAVEAS      = 'saveas'

    def __init__(self):
        threading.Thread.__init__(self)
        self.rdb = redis.Redis()
        self.setName('Saver '+ self.getName())

    def run(self):
        while 1:
            item = self.rdb.lpop(self.RDB_SAVE)
            if item is None:
                sleep = 0.01
                #logging.info('%r get None, sleep %s', self.getName(), sleep)
                time.sleep(sleep)
                continue
            try:
                info = marshal.loads(item)
                urltype, url, headers, content = info['urltype'], info['url'], info['headers'], info['content']
                logging.info('begin save type=%r, url=%r', urltype, url)
                profile.save(urltype, url, headers, content)
                logging.info('end save type=%r, url=%r', urltype, url)
            except Exception, e:
                logging.exception('Error: %s', e)

def main():
    saver = Saver()
    saver.start()
    saver.join()

if __name__ == '__main__':
    main()

