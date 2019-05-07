#coding=utf-8

import sys
import web
import router.router as router
from decouple import config
import task.async_sql_exec as async_sql_exec_task
import task.collect_department as collect_department_task
import task.cron_judger as cron_judger_task
import task.cron_executor as cron_executor_task
import task.index_cal as index_cal_task
import task.auto_verify as auto_verify_task
import task.session_clean as session_clean_task
import task.check_defunct as check_defunct_task

sys.argv.append(config('PORT'))
urls = router.routers
app = web.application(urls, globals())
web.config.session_parameters['timeout'] = config('SESSION_EXPIRE', cast=int) 
session = web.session.Session(app, web.session.DiskStore(config('SESSION_PATH')))

def session_hook():
    web.ctx.session = session
    
app.add_processor(web.loadhook(session_hook))
application = app.wsgifunc()

if __name__ == '__main__': 
    #收集一下部门信息
    if config('COLLECT_DEPART_TASK_ENABLE') == 'true': collect_department_task.start()
    #启动异步执行sql的任务
    if config('ASYNC_EXEC_SQL_TASK_ENABLE') == 'true': async_sql_exec_task.start()
    #启动cron_judger任务
    if config('CRON_JUDGER_ENABLE') == 'true': cron_judger_task.start()
    #启动归档执行任务
    if config('CRON_EXECUTOR_ENABLE') == 'true':cron_executor_task.start()
    #启动索引使用的统计任务
    if config('INDEX_CAL_TASK_ENABLE') == 'true':index_cal_task.start()
    #启动自动审核任务
    if config('AUTO_VERIFY_TASK_ENABLE') == 'true': auto_verify_task.start()
    #session清理任务
    session_clean_task.start()
    #僵尸进程检测任务
    if config('CHECK_DEFUNCT_TASK_ENABLE') == 'true': check_defunct_task.start()
    #启动ui
    web.config.debug = False
    app.run()