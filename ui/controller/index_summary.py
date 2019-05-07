#coding=utf-8

from common import *
import sys
sys.path.append('../')
from decouple import config
import demjson

class index(Guest):
    def handle(self):
        indexs = []
        try:
            f = open(config('INDEX_CAL_FILE'), 'r')
            content = f.read()
            f.close()
            indexs = demjson.decode(content)
        except Exception as ex:
            pass
        self.data['index_list'] = indexs
        return self.render().index_summary(data=self.data)