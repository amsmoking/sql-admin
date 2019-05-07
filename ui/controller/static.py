#coding=utf-8

from common import *

class index(common):
    def GET(self, file):
        web.seeother('/static/'+file)