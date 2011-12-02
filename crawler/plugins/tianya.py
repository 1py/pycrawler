#!/usr/bin/env python
# coding:utf-8

import sys, os, re, time
import urlparse
import logging
import lxml.etree

__domain__ = ['www.tianya.cn']

def escapepath(filename):
    m = dict(zip('\/:*?"<>| ', u'＼／：＊？＂＜＞｜　'))
    return ''.join(m.get(x, x) for x in filename)

def parse(info):
    url, headers, content = info['url'], info['headers'], info['content']
    assert urlparse.urlparse(url).netloc in __domain__
    tree = lxml.etree.fromstring(content, lxml.etree.HTMLParser())
    if re.search(r'http://www.tianya.cn/\w+/content/.+?.shtml', url):
        louzhu = info.get('louzhu')
        index = info.get('index', 1)
        if not louzhu:
            louzhu = tree.xpath("//a[starts-with(@href, 'http://my.tianya.cn/name/')]/text()")[0].strip()
            logging.info('xpath get louzhu name=%r', louzhu)
        nexturls = tree.xpath("//div[@class='pages']/em[@class='current']/following-sibling::a/@href")
        if nexturls:
            return {'save':True, 'index':index, 'louzhu':louzhu, 'download':[{'url':nexturls[0], 'louzhu':louzhu, 'index':index+1}]}
        else:
            return {'save':True, 'index':index, 'louzhu':louzhu}
    else:
        return {}

def save(info):
    url, headers, content, index, louzhu = info['url'], info['headers'], info['content'], info['index'], info['louzhu']
    assert urlparse.urlparse(url).netloc in __domain__
    tree = lxml.etree.fromstring(content, lxml.etree.HTMLParser())
    firstauthor = tree.xpath("//a[starts-with(@href, 'http://my.tianya.cn/name/')]/text()")[0].strip()
    allpost = [lxml.etree.tounicode(x, method='text') for x in tree.xpath("//div[@class='allpost']/div[@class='post']")]
    allname = [firstauthor] + tree.xpath("//div[@class='allpost']/table//a/text()")
    assert len(allpost) == len(allname)
    filename = escapepath(u'%02d.txt' % index)
    text = '\n'.join(post for name,post in zip(allname, allpost) if name==louzhu)
    with open(filename, 'wb') as fp:
        fp.write(text.encode('utf8'))

