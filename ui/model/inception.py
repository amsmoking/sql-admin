#coding=utf-8

from decouple import config
import sys
sys.path.append('../')
import logger.logger as log

def getIdcByHostname(hostname):
    '''
    成功返回idc, None
    否则返回'', 错误信息
    '''
    idc = ''
    err = None
    try:
        idc = hostname.split('-')[0]
    except Exception, ex:
        err = str(ex)
    return idc, err
    
def getIncHostPortByIdc(idc):
    inc_host = ''
    inc_port = ''
    if idc == 'bjxg':
        inc_host = config('INCEPTION_HOST')
        inc_port = config('INCEPTION_PORT')
    elif idc == 'pingan':
        inc_host = config('PINGAN_INCEPTION_HOST')
        inc_port = config('PINGAN_INCEPTION_PORT')
    else:
        pass
    log.info("get inception addr, idc:%s, host:%s, port:%s" % (idc, inc_host, inc_port))
    return inc_host, int(inc_port)