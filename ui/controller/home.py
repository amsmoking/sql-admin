#coding=utf-8

from common import *
import sys
sys.path.append('../')
from model.order import OrderModel, ORDER_STATUS_AGREE_SUCCED, ORDER_STATUS_AGREE_FAILED

class index(Guest):
    def handle(self):
        return self.render().flot(data=self.data)