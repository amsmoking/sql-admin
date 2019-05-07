import proxy

print proxy.test_privilege('127.0.0.1', 3306, 'inception', 'xxxx', '', '192.168.1.2', 'bjxg', is_grant = True)