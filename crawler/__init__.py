#!/usr/bin/env python
# coding:utf-8

import sys, os, re, time
import logging
import copy, marshal
import signal
import threading
try:
    import lxml.etree
except ImportError:
    logging.critical('import lxml.etree fail')
    sys.exit(-1)
try:
    import redis
except ImportError:
    logging.critical('import redis fail')
    sys.exit(-1)
try:
    import requests
except ImportError:
    logging.critical('import requests fail')
    sys.exit(-1)
try:
    import readability
except ImportError:
    logging.critical('import readability fail')
    sys.exit(-1)

from .plugins import _load_plugins
from .plugins import plugins_parse, plugins_save

logging.basicConfig(level=logging.INFO, format='%(levelname)s - - %(asctime)s %(message)s', datefmt='[%d/%b/%Y %H:%M:%S]')

class Common(object):

    def __init__(self):
        self.REDIS_IP          = '127.0.0.1'
        self.REDIS_PORT        = 6379

        self.REDIS_DOWNLOAD    = 'download'
        self.REDIS_DOWNLOADING = 'downloading'
        self.REDIS_DOWNLOADED  = 'downloaded'
        self.REDIS_SAVE        = 'save'

        self.DOWNLOAD_SLEEP       = 1.0
        self.DOWNLOAD_RETRY       = 3
        self.DOWNLOAD_THREADS     = 1

        self.PARSE_SLEEP          = 1.0
        self.PARSE_THREADS        = 1

        self.SAVE_SLEEP           = 1.0
        self.SAVE_THREADS         = 1

common = Common()

class Worker(threading.Thread):

    def __init__(self, *args, **kwargs):
        threading.Thread.__init__(self, *args, **kwargs)
        self.redis_client = redis.Redis(host=common.REDIS_IP, port=common.REDIS_PORT)
        self.setName('[%s %s]' %(self.__class__, self.getName()))

class Downloader(Worker):

    def run(self):
        self.requests = requests.Session()
        while 1:
            item = self.redis_client.rpop(common.REDIS_DOWNLOAD)
            if item is None:
                time.sleep(common.DOWNLOAD_SLEEP)
                continue
            try:
                info = marshal.loads(item)
                url = info['url']
                info['retry'] = retry = info.get('retry', 0) + 1
                logging.info('%s try process url=%r, retry=%r', self.getName(), url, retry)
                if retry > common.DOWNLOAD_RETRY:
                    logging.info('%s process url=%r retry=%r>3, continue', self.getName(), url, retry)
                    continue
                self.redis_client.zadd(common.REDIS_DOWNLOADING, item, 1)
                response = self.requests.get(url)
                self.redis_client.zrem(common.REDIS_DOWNLOADING, item)
                info['headers'] = dict(response.headers)
                info['content'] = response.content
                self.redis_client.lpush(common.REDIS_DOWNLOADED, marshal.dumps(info))
            except Exception, e:
                logging.exception('Exception Error: %s', e)
                self.redis_client.zrem(common.REDIS_DOWNLOADING, item)
                self.redis_client.lpush(common.REDIS_DOWNLOAD, marshal.dumps(info))

class Parser(Worker):

    def run(self):
        while 1:
            item = self.redis_client.rpop(common.REDIS_DOWNLOADED)
            if item is None:
                time.sleep(common.PARSE_SLEEP)
                continue
            try:
                info = marshal.loads(item)
                url, headers, content = info['url'], info['headers'], info['content']
                logging.info('%s try process url=%r', self.getName(), url)
                result = plugins_parse(info)
                if result.get('download'):
                    for downloadinfo in result.get('download'):
                        logging.info('parse need download info: %r', downloadinfo)
                        self.redis_client.lpush(common.REDIS_DOWNLOAD, marshal.dumps(downloadinfo))
                if result.get('save'):
                    info.update(result)
                    logging.info('%s send save info to saver url=%r', self.getName(), url)
                    self.redis_client.lpush(common.REDIS_SAVE, marshal.dumps(info))
                logging.info('%s end process url=%r', self.getName(), url)
            except Exception, e:
                logging.exception('Error: %s', e)

class Saver(Worker):

    def run(self):
        while 1:
            item = self.redis_client.rpop(common.REDIS_SAVE)
            if item is None:
                time.sleep(common.SAVE_SLEEP)
                continue
            try:
                info = marshal.loads(item)
                url = info['url']
                logging.info('%s try process url=%r', self.getName(), url)
                plugins_save(info)
                logging.info('%s try process url=%r OK', self.getName(), url)
            except Exception, e:
                logging.exception('Error: %s', e)

def main():
    if os.name == 'posix':
        signal.signal(signal.SIGHUB, lambda n,e:_load_plugins())
    threads = []
    for i in xrange(common.DOWNLOAD_THREADS):
        t = Downloader()
        t.start()
        threads.append(t)
    for i in xrange(common.PARSE_THREADS):
        t = Parser()
        t.start()
        threads.append(t)
    for i in xrange(common.SAVE_THREADS):
        t = Saver()
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

if __name__ == '__main__':
    main()

