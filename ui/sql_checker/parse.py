#coding=utf-8
import sqlparse

ALLOW_KEYWORDS = [
    'SELECT',
    'SHOW',
    'USE',
    'EXPLAIN',
    'DESC',
]

def get_sql_keywords(sql):
    res = sqlparse.parse(sql)
    stmt = res[0]
    kws = []
    for token in stmt.tokens:
        print token
        token = str(token).upper().strip()
        if token == '': continue
        kws.append(token)
    return kws

def not_all_execute_kw(sql):
    kws = get_sql_keywords(sql)
    kw = kws[0]
    if kw not in ALLOW_KEYWORDS:
        return kw
    return None

def get_src_sql_keywords(sql):
    res = sqlparse.parse(sql)
    stmt = res[0]
    kws = []
    for token in stmt.tokens:
        token = str(token).strip()
        if token == '': continue
        kws.append(token)
    return kws

def get_table_by_select_sql(sql):
    '''
    返回sql中的表名字
    找到了返回表名
    否则返回None
    '''
    kws = get_src_sql_keywords(sql)
    table = None
    lastKw = ''
    for kw in kws:
        if lastKw == 'FROM':
            table = kw
            table = table.replace("`", '')
            return table
        if kw.upper() == 'FROM':
            lastKw = 'FROM'
    return table