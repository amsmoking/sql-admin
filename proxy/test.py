#coding=utf-8

import rpyc
from decouple import config
conn = rpyc.connect('127.0.0.1', config('PORT'))
res = conn.root.test_conn('127.0.0.1', 3306, 'xdev', 'xdev')
print res
res = conn.root.test_privilege('127.0.0.1', 3306, 'xdev', 'xdev', 'xcrypto', '127.0.0.1', is_grant = True)
print res
conn.close()