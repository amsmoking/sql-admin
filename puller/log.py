#coding=utf-8

from decouple import config
from agileutil.log import Log

output_tag = False
if config('LOG_OUTPUT').lower() == 'true':
    output_tag = True
if config('LOG_OUTPUT').lower() == 'false':
    output_tag = False

logger = Log(config('LOG_FILE'))
logger.setOutput(output_tag)

def info(log_info):
    logger.info(log_info)

def warning(log_info):
    logger.warning(log_info)

def error(log_info):
    logger.error(log_info)