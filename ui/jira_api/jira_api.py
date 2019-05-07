#coding=utf-8

'''
这里调用jira api创建issue
参考:
https://developer.atlassian.com/server/jira/platform/jira-rest-api-examples/
https://developer.atlassian.com/cloud/jira/platform/rest/#api-api-2-issue-issueIdOrKey-transitions-post

curl -D- -u 用户名:密码 -X POST --data '{"fields": {"project":{ "key": "OP"},"summary": "jira api test","description": "create issue test","components":[{"name":"MySQL"}], "issuetype": {"name":"任务"}}}' -H "Content-Type: application/json" http://xxxxx/rest/api/2/issue/
'''

import requests
import demjson

def create_issue(url, username, password, project_key = 'OP', issuetype=u'任务', components='MySQL', summary = '', description = ''):
    '''
    url: http://xxxxxx/rest/api/2/issue/
    '''
    #截短字符串，避免太长导致jira接口调用失败
    summary = summary[0:1024]
    description = description[0:1024]
    headers = {'Content-Type': 'application/json'}
    params = {
        'fields' : {
            'project': { 'key': project_key},
            'summary' : summary,
            'components' : [{'name': components}],
            'description' : description,
            'issuetype' : {"name": issuetype}
        }
    }
    params = demjson.encode(params)
    s = requests.Session()
    s.headers.update(headers)
    s.auth = (username, password)
    r = s.post(url, data=params)
    return r.status_code, r.text

def reslove_issue(url, username, password, issue_key, trans_id):
    '''
    url: https://xxxx/rest/api/2/issue/issueIdOrKey/transitions
    '''
    headers = {
        'Content-Type': 'application/json',
        'Accept' : 'application/json'
    }
    params = {
        'transition' : {
            'id' : trans_id
        }
    }
    params = demjson.encode(params)
    s = requests.Session()
    s.headers.update(headers)
    s.auth = (username, password)
    r = s.post(url, data=params)
    return r.status_code, r.text

def create_comment(url, username, password, issue_key, comment = ''):
    '''
    url: http://kelpie9:8081/rest/api/2/issue/QA-31/comment
    '''
    #截短字符串，避免太长导致jira接口调用失败
    comment = comment[0:1024]
    url = url + issue_key + '/comment'
    headers = {'Content-Type': 'application/json'}
    params = {
        'body' : comment,
    }
    params = demjson.encode(params)
    s = requests.Session()
    s.headers.update(headers)
    s.auth = (username, password)
    r = s.post(url, data=params)
    return r.status_code, r.text