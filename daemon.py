#!/usr/bin/env python
# coding:utf-8

import sys, os, re, time
import logging
import glob

logging.basicConfig(level=0, format='%(levelname)s - - %(asctime)s %(message)s', datefmt='[%d/%b/%Y %H:%M:%S]')

def main():
    import crawler
    crawler.common.DOWNLOAD_THREADS = 10
    crawler.main()

if __name__ == '__main__':
    main()

