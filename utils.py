#!/usr/bin/env python
# coding:utf-8

import sys, os, re, time
import logging
import marshal, zlib

logging.basicConfig(level=logging.INFO, format='%(levelname)s - - %(asctime)s %(message)s', datefmt='[%d/%b/%Y %H:%M:%S]')

class DataBase(object):

    def __init__(self):
        self.conn = MySQLdb.connect(host='localhost',user='root', passwd='mac8.6', db='article')

    def exec_sql(self, sql):
        cursor = self.conn.cursor()
        result = cursor.execute(sql,param)
        cursor.close()
        return result

    def close(self):
        self.conn.close()


db = DataBase()

if __name__ == '__main__':
    main()

