#!/usr/bin/env python
# coding:utf-8

import sys, os, re, time
import urlparse, urllib
import logging
import lxml.etree

__domain__ = ['www.tianya.cn']

def escapepath(filename):
    m = dict(zip('\/:*?"<>| ', u'＼／：＊？＂＜＞｜　'))
    return ''.join(m.get(x, x) for x in filename)

def parse(info):
    url, content = info['url'], info['content']
    assert urlparse.urlparse(url).netloc in __domain__
    tree = lxml.etree.fromstring(content, lxml.etree.HTMLParser())
    result = {}
    if re.search(r'http://www.tianya.cn/publicforum/content/.+?.shtml', url):
        if 'louzhu' in info:
            louzhu = info['louzhu']
            index  = info['index']
            fromurl = info['fromurl']
        else:
            louzhu = tree.xpath("//a[starts-with(@href, 'http://my.tianya.cn/name')]/text()")[0].strip()
            index = 1
            fromurl = url
        firstauthor = tree.xpath("//a[starts-with(@href, 'http://my.tianya.cn/name')]/text()")[0].strip()
        allpost = [lxml.etree.tounicode(x, method='text') for x in tree.xpath("//div[@class='allpost']/div[@class='post']")]
        allname = [firstauthor] + tree.xpath("//div[@class='allpost']/table//a/text()")
        assert len(allpost) == len(allname)
        text = '\n'.join(post for name,post in zip(allname, allpost) if name==louzhu)
        filename = u'save/%s/%02d.txt' % (urllib.quote_plus(fromurl), index)
        result['save'] = [{'url':url, 'text': text, 'filename':filename}]
        nexturls = tree.xpath("//div[@class='pages']/em[@class='current']/following-sibling::a/@href")
        if nexturls:
            result['download'] = [{'url':nexturls[0], 'louzhu':louzhu, 'index':index+1, 'fromurl':fromurl}]
    elif re.search(r'http://www.tianya.cn/techforum/content/.+?.shtml', url):
        if 'louzhu' in info:
            louzhu = info['louzhu']
            index  = info['index']
            fromurl = info['fromurl']
        else:
            louzhu = tree.xpath("//a[starts-with(@href, 'http://my.tianya.cn/')]/text()")[0].strip()
            index = 1
            fromurl = url
        allpost = [lxml.etree.tounicode(x, method='text') for x in tree.xpath("//div[@id='pContentDiv']/div[@class='item']/div[@class='post']")]
        allname = tree.xpath("//div[@id='pContentDiv']/div[@class='item']/div[@class='vcard']/a[starts-with(@href, 'http://my.tianya.cn/')]/text()")
        assert len(allpost) == len(allname)
        text = '\n'.join(post for name,post in zip(allname, allpost) if name==louzhu)
        filename = u'save/%s/%02d.txt' % (urllib.quote_plus(fromurl), index)
        result['save'] = [{'url':url, 'text': text, 'filename':filename}]
        nexturls = tree.xpath("//form[@id='pageForm']/em[@class='current']/following-sibling::a/@href")
        if nexturls:
            result['download'] = [{'url':nexturls[0], 'louzhu':louzhu, 'index':index+1, 'fromurl':fromurl}]
    else:
        pass
    return result

def save(info):
    url, text, filename = info['url'], info['text'], info['filename']
    assert urlparse.urlparse(url).netloc in __domain__
    try:
        os.makedirs(os.path.dirname(filename))
    except:
        pass
    with open(filename, 'wb') as fp:
        fp.write(text.encode('utf8'))

