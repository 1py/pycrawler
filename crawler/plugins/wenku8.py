#!/usr/bin/env python
# coding:utf-8

import sys, os, re, time
import lxml.etree

TAG = os.path.splitext(os.path.basename(__file__))[0]

def urlrefine(url):
    pass

def encoding(info):
    return 'gb18030'

def parse(info):
    url, tag, headers, content = info['url'], info['tag'], info['headers'], info['content']
    assert tag == TAG
    tree = lxml.etree.fromstring(content, lxml.etree.HTMLParser())
    if re.search(r'http://www.wenku8.cn/novel/\d+/\d+/index\.htm', url):
        links = tree.xpath("//td[@class='ccss']/a/@href")
        return {'links':links}
    elif re.search(r'http://www.wenku8.cn/novel/\d+/\d+/\d+.htm', url):
        save = lxml.etree.tounicode(tree.xpath("//div[@id='content']")[0], method='text')
        savetitle = lxml.etree.tounicode(tree.xpath("//div[@id='title']")[0], method='text')
        return {'save':save, 'savetitle':savetitle}
    else:
        return {}

def escapepath(filename):
    m = dict(zip('\/:*?"<>| ', u'＼／：＊？＂＜＞｜　'))
    return ''.join(m.get(x, x) for x in filename)

def save(info):
    url, tag = info['url'], info['tag']
    assert tag == TAG
    filename = escapepath(u'%s.txt' % info['savetitle'].strip())
    with open(filename, 'wb') as fp:
        fp.write(info['save'].encode('utf8'))

