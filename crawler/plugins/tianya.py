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
    url, headers, content = info['url'], info['headers'], info['content']
    assert urlparse.urlparse(url).netloc in __domain__
    tree = lxml.etree.fromstring(content, lxml.etree.HTMLParser())
    result = {}
    if re.search(r'http://www.tianya.cn/publicforum/content/.+?.shtml', url):
        louzhu = info.get('louzhu')
        index = info.get('index', 1)
        if not louzhu:
            louzhu = tree.xpath("//a[starts-with(@href, 'http://my.tianya.cn/name')]/text()")[0].strip()
            logging.info('xpath get louzhu name=%r', louzhu)
        result = {}
        result['save'] = [{'url':url, 'content': content, 'index':index, 'louzhu':louzhu}]
        nexturls = tree.xpath("//div[@class='pages']/em[@class='current']/following-sibling::a/@href")
        if nexturls:
            result['download'] = [{'url':nexturls[0], 'louzhu':louzhu, 'index':index+1}]
    elif re.search(r'http://www.tianya.cn/techforum/content/.+?.shtml', url):
        louzhu = info.get('louzhu')
        index = info.get('index', 1)
        if not louzhu:
            louzhu = tree.xpath("//a[starts-with(@href, 'http://my.tianya.cn/')]/text()")[0].strip()
            logging.info('xpath get louzhu name=%r', louzhu)
        result = {}
        result['save'] = [{'url':url, 'content': content, 'index':index, 'louzhu':louzhu}]
        nexturls = tree.xpath("//form[@id='pageForm']/em[@class='current']/following-sibling::a/@href")
        if nexturls:
            result['download'] = [{'url':nexturls[0], 'louzhu':louzhu, 'index':index+1}]
    else:
        pass
    return result

def save(info):
    url, content, index, louzhu = info['url'], info['content'], info['index'], info['louzhu']
    assert urlparse.urlparse(url).netloc in __domain__
    tree = lxml.etree.fromstring(content, lxml.etree.HTMLParser())
    if re.search(r'http://www.tianya.cn/publicforum/content/.+?.shtml', url):
        firstauthor = tree.xpath("//a[starts-with(@href, 'http://my.tianya.cn/')]/text()")[0].strip()
        allpost = [lxml.etree.tounicode(x, method='text') for x in tree.xpath("//div[@class='allpost']/div[@class='post']")]
        allname = [firstauthor] + tree.xpath("//div[@class='allpost']/table//a/text()")
        assert len(allpost) == len(allname)
        filename = escapepath(u'%s_%s_%02d.txt' % ('tianya', urllib.quote_plus(url), index))
        text = '\n'.join(post for name,post in zip(allname, allpost) if name==louzhu)
        dirname = 'save/'+urlparse.urlparse(url).netloc
        if not os.path.exists(dirname):
            os.mkdir(dirname)
        with open(dirname+'/'+filename, 'wb') as fp:
            fp.write(text.encode('utf8'))
    elif re.search(r'http://www.tianya.cn/techforum/content/.+?.shtml', url):
        allpost = [lxml.etree.tounicode(x, method='text') for x in tree.xpath("//div[@id='pContentDiv']/div[@class='item']/div[@class='post']")]
        allname = tree.xpath("//div[@id='pContentDiv']/div[@class='item']/div[@class='vcard']/a[starts-with(@href, 'http://my.tianya.cn/')]/text()")
        assert len(allpost) == len(allname)
        filename = escapepath(u'%02d.txt' % index)
        text = '\n'.join(post for name,post in zip(allname, allpost) if name==louzhu)
        dirname = os.path.join('save', urlparse.urlparse(url).netloc, urllib.quote_plus(url))
        try:
            os.makedirs(dirname)
        except:
            pass
        with open(dirname+'/'+filename, 'wb') as fp:
            fp.write(text.encode('utf8'))
    else:
        pass

