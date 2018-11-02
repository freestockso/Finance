# -*- coding: utf-8 -*-

import logging

class Logger(object):

    def __init__(self, name = 'log.txt'):

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(level = logging.INFO)
        handler = logging.FileHandler(name)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def log(self,info):
        self.logger.info(info)


if __name__ == '__main__':
    mongo = Logger('mongodb.txt')
    mongo.log('hello world')
    mongo.log('hello world1')