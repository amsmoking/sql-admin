#coding=utf-8

import rpyc
import copy
from decouple import config
import pickle
import sys
sys.path.append('../')
import logger.logger as log

def get_host_port_by_idc(idc):
    host = ''
    port = 0
    if idc == 'bjxg':
        host = config('BJXG_PROXY_HOST')
        port = int(config('BJXG_PROXY_PORT'))
    elif idc == 'pingan':
        host = config('PINGAN_PROXY_HOST')
        port = int(config('PINGAN_PROXY_PORT'))
    else:
        pass
    return host, port

def test_conn(host, port, user, pwd, idc):
    rpc_host, rpc_port = get_host_port_by_idc(idc)
    conn = rpyc.connect(rpc_host, rpc_port)
    err = conn.root.test_conn(host, port, user, pwd)
    conn.close()
    return err

def get_on_ip_by_idc(idc):
    onIp = ''
    if idc == 'bjxg':
        onIp = config('BJXG_PROXY_HOST')
    elif idc == 'pingan':
        onIp = config('PINGAN_PROXY_HOST')
    else:
        pass
    return onIp

def test_privilege(host, port, user, pwd, dbname, onIp, idc, is_grant = False):
    is_grant = False
    rpc_host, rpc_port = get_host_port_by_idc(idc)
    conn = rpyc.connect(rpc_host, rpc_port)
    onIp = get_on_ip_by_idc(idc)
    res = conn.root.test_privilege(host, port, user, pwd, dbname, onIp, is_grant)
    conn.close()
    ret = pickle.loads(res)
    #log.info("test_privilege host:%s, port:%s, user:%s, pwd:%s, dbname:%s, onIp:%s, idc:%s, is_grant:%s, ret:%s" % (
    #    host, port, user, pwd, dbname, onIp, idc, str(is_grant), str(ret)
    #))
    return ret

def safe_test_privilege(host, port, user, pwd, dbname, onIp, idc, is_grant = False):
    try:
        return test_privilege(host, port, user, pwd, dbname, onIp, idc, is_grant)
    except Exception, ex:
        return None, None, None, str(ex)