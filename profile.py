#!/usr/bin/env python
# coding:utf-8

import sys, os, re, time
import logging
import marshal, zlib
import socket, httplib, urllib2, urlparse
import thread, threading
import redis
import urlparse
import lxml.etree
#import utils

logging.basicConfig(level=0, format='%(levelname)s - - %(asctime)s %(message)s', datefmt='[%d/%b/%Y %H:%M:%S]')

def __callback(method, urltype, url, headers, content, *args):
    profile = __import__('profile')
    attr = '%s_%s' % (method, urltype)
    callback = getattr(profile, attr)
    if 'gzip' in headers.get('content-encoding', ''):
        content = content.decode('zlib')
    result = callback(url, headers, content, *args)
    return result

def parse(urltype, url, headers, content, *args):
    return __callback('parse', urltype, url, headers, content, *args)

def save(urltype, url, headers, content, *args):
    return __callback('save', urltype, url, headers, content, *args)

def saveas(urltype, url, headers, content, *args):
    return __callback('saveas', urltype, url, headers, content, *args)

def html2text(html):
    tree = lxml.etree.fromstring(html, lxml.etree.HTMLParser())if isinstance(html, basestring) else html
    for skiptag in ('//script', '//iframe'):
        for node in tree.xpath(skiptag):
            node.getparent().remove(node)
    return lxml.etree.tounicode(tree, method='text')

def escapesql(text):
    return re.sub('''(['"])''', r'\\\1', text)

def escapepath(filename):
    m = dict(zip('\/:*?"<>| ', u'＼／：＊？＂＜＞｜　'))
    return ''.join(m.get(x, x) for x in filename)

def parse_wordpress_page(url, headers, content):
    links, save, saveas = [], '', []
    tree = lxml.etree.fromstring(content.decode('utf8'), lxml.etree.HTMLParser())
    links += set('wordpress_post %s' % urlparse.urljoin(url, x) for x in tree.xpath("//h2/a/@href"))
    links += set('wordpress_page %s' % urlparse.urljoin(url, x) for x in tree.xpath("//a[contains(text(), 'Older')]/@href"))
    return links, save, saveas

def parse_wordpress_post(url, headers, content):
    links, save, saveas = [], '', []
    tree = lxml.etree.fromstring(content.decode('utf8'), lxml.etree.HTMLParser())
    subtrees = tree.xpath("//div[starts-with(@id, 'post-')]") or tree.xpath("//div[starts-with(@id, 'post')]")
    save = max([lxml.etree.tostring(x) for x in subtrees], key=len)
    if save < 1024:
        save = ''
    save = save.encode('utf8')
    return links, save, saveas

def save_wordpress_post(url, headers, content):
    tree = lxml.etree.fromstring(content.decode('utf8'), lxml.etree.HTMLParser())
    text = html2text(content).strip().encode('utf8')
    title = ''
    for query in ('//h2/a/text()', '//h1/a/text()', '//h3/a/text()'):
        titles = tree.xpath(query)
        if titles:
            title = titles[0]
            break
    if not title:
        title = text.splitlines()[0]
    #sql = "INSERT INTO article (Title, Description, Body) VALUES('%s', '', '%s')" % (escapesql(title), escapesql(text))
    #result = utils.db.exec_sql(sql)
    rootdir, dirname = 'wordpress_post', urlparse.urlparse(url).netloc
    if not os.path.exists(rootdir):
        os.mkdir(rootdir)
    if not os.path.exists(rootdir+'/'+dirname):
        os.mkdir(rootdir+'/'+dirname)
    filename = u'%s/%s/%s.txt' % (rootdir, dirname, escapepath(title.decode('utf8')))
    with open(filename, 'wb') as fp:
        fp.write(text)

def parse_wenku8_page(url, headers, content):
    links, save, saveas = [], '', []
    tree = lxml.etree.fromstring(content.decode('gb18030', 'ignore'), lxml.etree.HTMLParser())
    links += set('wenku8_packtxt http://www.wenku8.cn/modules/article/packtxt.php?id=%s' % x.split('=')[-1] for x in tree.xpath("//table[@class='grid']//a[contains(@href, 'articleinfo.php')]/@href"))
    links += set('wenku8_page %s' % urlparse.urljoin(url, x) for x in tree.xpath("//div[@id='pagelink']//a[@class='next']/@href"))
    return links, save, saveas

def parse_wenku8_packtxt(url, headers, content):
    links, save, saveas = [], '', []
    html = content.decode('gb18030', 'ignore')
    tree = lxml.etree.fromstring(content.decode('gb18030', 'ignore'), lxml.etree.HTMLParser())
    title = escapepath(re.search(ur'《<.+?>\s*(.+?)\s*<.+?>》', html).group(1))
    infos = [(x.xpath('td[1]/text()')[0].strip(), re.findall(r'http://.+?charset=gbk', x.xpath('td[3]/script[1]/text()')[0])[0]) for x in tree.xpath("//table[@class='grid']/tr")[1:]]
    for subtitle, url in infos:
        saveas.append('wenku8_downtxt %s_%s %s' % (escapepath(title), escapepath(subtitle), url))
    return links, save, saveas

def saveas_wenku8_downtxt(url, headers, content, title):
    filename = u'saveas_wenku8_downtxt/%s.txt' % title.decode('utf8')
    with open(filename, 'wb') as fp:
        fp.write(content)


