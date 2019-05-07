#coding=utf-8

import sys
sys.path.append("../")
from model.order import OrderModel
from model.user_model import UserModel
from decouple import config
import agileutil.mail as mail
import jira_api.jira_api as jira_api
import logger.logger as log
import sqlparse
import demjson
import agileutil.util as util
from model.order import ORDER_STATUS_NO_COMMIT

def formatSql(sql):
    if '\n' in sql: return sql
    formatSqlString = sqlparse.format(sql, reindent=True, keyword_case='upper')
    return formatSqlString

def notify_admin_by_send_mail(order_id):
    orderModel = OrderModel()
    order = orderModel.load(order_id)
    req_user = order['req_user']
    title = u'MySQL上线申请'
    content = u'用户' + unicode(req_user) + '提交了一个申请，请登入审批。'
    from_addr = config('NOTIFY_FROM_ADDR')
    #得到所有管理员
    admin_users = UserModel().getAllAdminUsers()
    mail_list = [user['mail'] for user in admin_users]
    to_addr = ','.join(mail_list)
    mail.send(
        from_addr=from_addr, 
        to_addr=to_addr, 
        host=config('SEND_MAIL_SERVER'),
        port=config('SEND_MAIL_PORT', cast=int),
        title=title,
        content=content
    )

def notify_jira(order_id, username, pwd):
    '''
    调用jira api创建issue
    url, username, password, project_key = 'OP', issuetype=u'任务', components='MySQL', summary = '', description = ''):
    '''
    #log.info("ready to notify, order_id:%s, username:%s, pwd:%s" % (str(order_id), str(username), str(pwd)))
    log.info("ready to notify, order_id:%s, username:%s" % (str(order_id), str(username)) )
    orderModel = OrderModel()
    order = orderModel.load(order_id)
    if order['issue_key'] != '' and order['issue_key'] != None:
        log.info("issue key exist, not call api")
        return
    req_user = order['req_user']
    reason = order['reason']
    sql = order['sql']
    sql = formatSql(sql)
    code = None
    resp = None
    #log.info("username:" + username)
    #log.info("password:" + pwd)
    url = config('JIRA_ISSUE_URL')
    sel_ip = order['sel_ip']
    order_port = str(order['sel_port'])
    db_name = order['sel_db_name']
    desp = ''
    port = config('PORT')
    deal_url = 'http://xxx.xxx.com/sql_order/index'
    #desp = desp + u"处理地址: " + config('JIRA_REDIRECT_URL') + "\r\n"
    desp = desp + u"处理地址: " + deal_url + "\r\n"
    #desp = desp + u"申请人: " + order['req_user'] + "\r\n"
    desp = desp + "MySQL IP: " + sel_ip + "\r\n"
    desp = desp + u"端口: " + unicode(order_port) + "\r\n"
    desp = desp + u"数据库: " + db_name + "\r\n"
    desp =  desp + "SQL语句:" + "\r\n"
    desp = desp + sql + "\r\n"
    summary = u'[SQL自助，工单号' + str(order_id) + "] "
    summary = summary + reason
    summary = summary[0:254]
    try:
        code, resp = jira_api.create_issue(
            url = url,
            username = username,
            password = pwd,
            summary = summary,
            description = desp
        )
    except Exception, ex:
        log.error("call jira api create issue exception:url:%s, code:%s, resp:%s, ex:%s" % (
            url, code, resp, str(ex)
        ))
        return
    log.info("after call jira api, url:%s, code:%s, resp:%s" % (url, code, resp))
    if str(code)[0:1] != '2':
        log.error("call jira api failed")
        return
    log.info("call jira api succed")
    #调用jira接口成功了,这时把在jira上创建的issue_key保存起来
    try:
        resp = demjson.decode(resp)
        issue_key = resp['key']
        orderModel.setIssueKey(order_id, issue_key)
        log.info("save issue key succed, issue_key:" + issue_key)
    except Exception, ex:
        log.error("save issue key exception:" + str(ex))
    return

def reslove_issue(order_id, username, pwd):
    '''
    调用jira api 解决issue
    '''
    orderModel = OrderModel()
    order = orderModel.load(order_id)
    issue_key = order['issue_key']
    code = None
    resp = None
    url = config('JIRA_RESLOVE_URL')
    url = url.replace('issueIdOrKey', issue_key)
    try:
        code, resp = jira_api.reslove_issue(
            url = url,
            username = username,
            password = pwd,
            issue_key = issue_key,
            trans_id = config('JIRA_RESLOVE_TRANS_ID', cast=int)
        )
    except Exception, ex:
        log.error("http request to reslove jira issue exception, url:%s, code:%s, resp:%s" % (
            url, code, resp
        ))
        return
    log.info("after call jira api, url:%s, code:%s, resp:%s" % (url, code, resp))
    if str(code)[0:1] != '2':
        log.error("call jira api failed")
        return
    log.info("call jira api succed")
    return

def add_comment(order_id, username, pwd, comment):
    '''
    调用jira api， 添加评论
    '''
    orderModel = OrderModel()
    order = orderModel.load(order_id)
    if order == None:
        log.error("jira add comment, order_id not found")
        return
    issue_key = order['issue_key']
    if issue_key == '' or issue_key == None:
        log.error("jira add comment, issue key is empty")
        return
    url = config('JIRA_ADD_COMMENT_URL')
    #create_comment(url, username, password, issue_key, comment = ''):
    code = 0
    resp = ''
    try:
        code, resp = jira_api.create_comment(url, username, pwd, issue_key, comment)
    except Exception, ex:
        log.error("jira api add comment exception:" + str(ex))
    log.info("after call jira api add comment, url:%s, code:%s, resp:%s" % (url, code, resp))

def send_alarm(title, content = ''):
    try:
        url = config('ALARM_URL')
        params = {
            'title' : title,
            'content' : content
        }
        code, resp = util.http(url, params, mtimeout=2)
        log.info("after send alarm, url:%s, code:%s, resp:%s" % (url, code, resp))
    except Exception as ex:
        log.error("send alarm exception:" + str(ex))