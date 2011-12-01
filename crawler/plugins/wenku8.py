#!/usr/bin/env python
# coding:utf-8

import sys, os, re, time
import urlparse
import lxml.etree

__domain__ = ['www.wenku8.cn']

def escapepath(filename):
    m = dict(zip('\/:*?"<>| ', u'＼／：＊？＂＜＞｜　'))
    return ''.join(m.get(x, x) for x in filename)

def parse(info):
    url, headers, content = info['url'], info['headers'], info['content']
    assert urlparse.urlparse(url).netloc in __domain__
    tree = lxml.etree.fromstring(content.decode('gb18030', 'ignore'), lxml.etree.HTMLParser())
    if re.search(r'http://www.wenku8.cn/novel/\d+/\d+/index\.htm', url):
        links = tree.xpath("//td[@class='ccss']/a/@href")
        return {'links':[{'url':link, 'index':i} for i, link in enumerate(links, 1)]}
    elif re.search(r'http://www.wenku8.cn/novel/\d+/\d+/\d+.htm', url):
        return {'save':True}
    else:
        return {}

def save(info):
    url, headers, content, index = info['url'], info['headers'], info['content'], info['index']
    assert urlparse.urlparse(url).netloc in __domain__
    tree = lxml.etree.fromstring(content.decode('gb18030', 'ignore'), lxml.etree.HTMLParser())
    text = lxml.etree.tounicode(tree.xpath("//div[@id='content']")[0], method='text')
    title = lxml.etree.tounicode(tree.xpath("//div[@id='title']")[0], method='text')
    filename = escapepath(u'%02d.%s.txt' % (index, title.strip()))
    with open(filename, 'wb') as fp:
        fp.write(text.encode('utf8'))

