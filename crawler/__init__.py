#!/usr/bin/env python
# coding:utf-8

import sys, os, re, time
import logging
import json
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
from .plugins import plugins_encoding, plugins_parse, plugins_save

logging.basicConfig(level=logging.INFO, format='%(levelname)s - - %(asctime)s %(message)s', datefmt='[%d/%b/%Y %H:%M:%S]')

class Common(object):

    def __init__(self):
        self.REDIS_IP          = '127.0.0.1'
        self.REDIS_PORT        = 6379

        self.REDIS_DOWNLOAD    = 'download'
        self.REDIS_DOWNLOADING = 'downloading'
        self.REDIS_DOWNLOADED  = 'downloaded'
        self.REDIS_SAVE        = 'save'

        self.REDIS_DEFAULT_TAG = 'default'

        self.DOWNLOAD_SLEEP       = 1.0
        self.DOWNLOAD_RETRY       = 3
        self.DOWNLOAD_THREADS     = 10

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
        while 1:
            item = self.redis_client.rpop(common.REDIS_DOWNLOAD)
            if item is None:
                time.sleep(common.DOWNLOAD_SLEEP)
                continue
            try:
                info = json.loads(item)
                url = info['url']
                info['tag'] = tag = info.get('tag', common.REDIS_DEFAULT_TAG)
                info['retry'] = retry = info.get('retry', 0) + 1
                logging.info('%s try process tag=%r, url=%r, retry=%r', self.getName(), tag, url, retry)
                if retry > common.DOWNLOAD_RETRY:
                    logging.info('%s process url=%r retry=%r>3, continue', self.getName(), url, retry)
                    continue
                self.redis_client.zadd(common.REDIS_DOWNLOADING, item, 1)
                response = requests.get(url)
                self.redis_client.zrem(common.REDIS_DOWNLOADING, item)
                info['headers'] = response.headers
                info['content'] = response.content
                if isinstance(info['content'], str):
                    info['content'] = info['content'].decode(plugins_encoding(info))
                self.redis_client.lpush(common.REDIS_DOWNLOADED, json.dumps(info))
            except Exception, e:
                logging.exception('Exception Error: %s', e)
                self.redis_client.zrem(common.REDIS_DOWNLOADING, item)
                self.redis_client.lpush(common.REDIS_DOWNLOAD, json.dumps(info))

class Parser(Worker):

    def run(self):
        while 1:
            item = self.redis_client.rpop(common.REDIS_DOWNLOADED)
            if item is None:
                time.sleep(common.PARSE_SLEEP)
                continue
            try:
                info = json.loads(item)
                url, tag, headers, content = info['url'], info['tag'], info['headers'], info['content']
                logging.info('%s try process tag=%r, url=%r', self.getName(), tag, url)
                result = plugins_parse(info)
                for link in result.get('links', []):
                    logging.info('parse out link: %r', link)
                    self.redis_client.lpush(common.REDIS_DOWNLOAD, json.dumps({'url':link, 'tag':tag}))
                if 'save' in result:
                    info.update(result)
                    logging.info('%s send save content to saver tag=%r, url=%r', self.getName(), tag, url)
                    self.redis_client.lpush(common.REDIS_SAVE, json.dumps(info))
                logging.info('%s end process tag=%r, url=%r', self.getName(), tag, url)
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
                info = json.loads(item)
                url, tag = info['tag'], info['url']
                logging.info('%s try process tag=%r, url=%r', self.getName(), tag, url)
                plugins_save(info)
                logging.info('%s try process tag=%r, url=%r OK', self.getName(), tag, url)
            except Exception, e:
                logging.exception('Error: %s', e)

def main():
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

