#coding=utf-8

'''
#一个索引中，列的最大个数，超过这个数目则报错
inception_max_key_parts=5
#在一个修改语句中，预计影响的最大行数，超过这个数就报错
inception_max_update_rows=100000
#一个表中，最大的索引数目，超过这个数则报错
inception_max_keys=16
#表示在建表或者建库时支持的字符集，如果需要多个，则用逗号分隔，影响的范围是建表、设置会话字符集、修改表字符集属性等
inception_support_charset=utf8mb4,utf8
#当char类型的长度大于这个值时，就提示将其转换为VARCHAR
inception_max_char_length=16
inception_check_column_default_value=1
#检查是不是支持BLOB字段，包括建表、修改列、新增列操作

#打开与关闭Inception对SQL语句中各种名字的检查，如果设置为ON，则如果发现名字中存在除数字、字母、下划线之外的字符时，会报Identifier "invalidname" is invalid, valid options: [a-z,A-Z,0-9,_].
inception_check_identifier=1

#这个参数实际上就是MySQL数据库原来的参数，因为Incpetion没有权限验证过程，那么为了实现更安全的访问，可以给Inception服务器的这个参数设置某台机器（Inception上层的应用程序）不地址，这样其它非法程序是不可访问的，那么再加上Inception执行的选项中的用户名密码，对MySQL就更加安全
bind_address


'''

VARIABLES_MAP = {
    #常用配置
    'inception_check_table_comment' : u'建表时，表没有注释，报错',
    'inception_check_column_comment' : u'建表时，列没有注释，报错',
    'inception_check_primary_key' : u'建表时，如果没有主键，报错',
    'inception_check_dml_where' : u'在DML语句中没有WHERE条件时，报错',
    'inception_check_index_prefix' : u'索引名字前缀不为"idx_"，唯一索引前缀不是"uniq_，报错',
    'inception_enable_autoincrement_unsigned' : u'自增列不是无符号型，报错',
    'inception_check_column_default_value' : u'在建表、修改列、新增列时，列属性没有默认值，报错',
    'inception_enable_identifer_keyword' : u'在SQL语句中，有标识符被写成MySQL的关键字，报错',
    'inception_enable_select_star' : u'Select*时，报错',

    'inception_enable_enum_set_bit' : u'支持enum,set,bit数据类型',
    'inception_check_autoincrement_init_value' : u'当建表时自增列的值指定的不为1，报错',
    #'inception_check_autoincrement_datatype' : u'当建表时自增列的类型不为int或者bigint时, 报错',
    'inception_check_timestamp_default' : u'建表时，如果没有为timestamp类型指定默认值，报错',
    'inception_check_autoincrement_name' : u'建表时，如果指定的自增列的名字不为ID，报错',
    'inception_merge_alter_table' : u'在多个改同一个表的语句出现时，报错，提示合成一个',


    #'inception_check_dml_limit' : u'在DML语句中使用了LIMIT时，报错',
    #'inception_check_dml_orderby' : u'在DML语句中使用了Order By时，报错',
    'inception_enable_foreign_key': u'支持外键',
    'inception_enable_not_innodb' : u'建表指定的存储引擎不为Innodb，报错',
    #'inception_enable_column_charset' : u'允许列自己设置字符集',
    'inception_read_only' : u'设置当前Inception服务器是不是只读的',

    #不常用配置
    'inception_enable_nullable': u'创建或者新增列时如果列为NULL，报错',
    #'inception_enable_partition_table' : u'是否支持分区表'
}

VARIABLES_SORTED = [
    'inception_check_table_comment',
    'inception_check_column_comment',
    'inception_check_column_default_value',
    'inception_check_primary_key',
    'inception_check_dml_where',
    'inception_check_index_prefix',
    'inception_enable_autoincrement_unsigned',
    'inception_enable_identifer_keyword',
    'inception_enable_select_star',

    'inception_enable_enum_set_bit',
    'inception_check_autoincrement_init_value',
    'inception_check_autoincrement_datatype',
    'inception_check_timestamp_default',
    'inception_check_autoincrement_name',
    'inception_merge_alter_table',

    'inception_check_dml_limit',
    'inception_check_dml_orderby',
    'inception_enable_foreign_key',
    'inception_enable_not_innodb',
    'inception_enable_column_charset',
    'inception_read_only',

    'inception_enable_nullable',
    'inception_enable_partition_table'
]

REVERSE_VARIABLE = [
    'inception_enable_identifer_keyword',
    'inception_enable_select_star',
    'inception_enable_not_innodb',
    'inception_enable_nullable',
    #'inception_check_table_comment',
    #'inception_check_column_comment',
    #'inception_check_column_default_value',
    #'inception_check_timestamp_default',
    #'inception_enable_foreign_key',
]

def filter_variables(rows = []):
    if rows == None or len(rows) == 0: return rows
    variables = []
    for row in rows:
        vari_name = row['Variable_name']
        val = row['Value']
        if VARIABLES_MAP.has_key(vari_name):
            variables.append(row)
    return variables

def file_zh_name(rows = []):
    if rows == None or len(rows) == 0: return rows
    for row in rows:
        vari_name = row['Variable_name']
        zh_name = u''
        try:
            zh_name = VARIABLES_MAP[vari_name]
        except:
            pass
        row['zh_name'] = zh_name
    return rows

def sort_by_important(rows = []):
    if rows == None or len(rows) == 0: return rows
    make_map = {}
    for row in rows:
        vari_name = row['Variable_name']
        make_map[vari_name] = row
    sorted_rows = []
    for vari_name in VARIABLES_SORTED:
        try:
            sorted_rows.append(
                make_map[vari_name]
            )
        except:
            pass
    return sorted_rows

def reverse_special_variable(obj):
    if obj == None: return
    if type(obj) != dict and type(obj) != list: return
    if type(obj) == list:
        #list
        rows = obj
        for row in rows:
            #MySQL关键字
            if row['Variable_name'] in REVERSE_VARIABLE:
                val = row['Value']
                print "vari:", row['Variable_name']
                print 'val:', row['Value']
                if val.upper() == 'OFF': row['Value'] = 'ON'
                else: row['Value'] = 'OFF'
    else:
        #dict
        for vari_name, val in obj.items():
            #MySQL关键字
            if vari_name in REVERSE_VARIABLE:
                to_status = ''
                if val.upper() == 'OFF': 
                    obj[vari_name] == 'ON'
                    to_status = 'ON'
                else:
                     obj[vari_name] == 'OFF'
                     to_status = 'OFF'
                obj[vari_name] = to_status
    return obj