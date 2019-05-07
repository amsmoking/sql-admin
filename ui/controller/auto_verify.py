#coding=utf-8

import sys
sys.path.append('../')
from common import *
from model.auto_verify_model import AutoVerifyModel

'''
DROP TABLE IF EXISTS `auto_verify`;
CREATE TABLE `auto_verify` (
    `id` int(11) unsigned NOT NULL AUTO_INCREMENT COMMENT 'id',
    `begin_time` varchar(255) NOT NULL DEFAULT '' COMMENT '起始时间',
    `end_time` varchar(255) NOT NULL DEFAULT '' COMMENT '结束时间',
    `enable` int(3) unsigned NOT NULL DEFAULT 0 COMMENT '状态, 0禁用,1启用',
    `is_send_mail` int(3) unsigned NOT NULL DEFAULT 0 COMMENT '是否发送邮件,0不发，1发',
    `tos` varchar(255) NOT NULL DEFAULT '' COMMENT '接收邮件的邮箱地址',
    PRIMARY KEY  (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT '自动审核表';
'''

class index(Admin):
    def handle(self):
        autoVerifyModel = AutoVerifyModel()
        autoVerify = AutoVerifyModel().loadAutoVerify()
        self.data['auto_verify'] = autoVerify
        return self.render().auto_verify(data = self.data)

class update(Admin):
    def handle(self):
        timeRange = self.req('time_range')
        enable = self.req('enable')
        isSendMail = self.req('is_send_mail')
        tos = self.req('tos')
        if enable == '1':
            if timeRange == '':
                return self.resp(errno=1, errmsg='请选择时间范围')
        beginTime, endTime = [item.strip() for item in timeRange.split('-')]
        autoVerifyModel = AutoVerifyModel()
        try:
            autoVerifyModel.updateAutoVerify(beginTime, endTime, enable, isSendMail, tos)
        except Exception as ex:
            return self.resp(errno=2, errmsg = str(ex))
        return self.resp()