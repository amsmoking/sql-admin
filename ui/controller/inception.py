#coding=utf-8

from common import *
import sys
sys.path.append('../')
import sql_checker.inception_variables as inception_variables
from sql_checker.inception import *

class config_index(Admin):
    def handle(self):
        #return ''
        inc_db = InceptionDB(host=config('INCEPTION_HOST'), port=config('INCEPTION_PORT', cast=int))
        variables = inc_db.loadVariables()
        variables = inception_variables.filter_variables(variables)
        variables = inception_variables.file_zh_name(variables)
        variables = inception_variables.sort_by_important(variables)
        variables = inception_variables.reverse_special_variable(variables)
        print 'variables', variables
        self.data['variables'] = variables
        return self.render().config_index(data = self.data)

class update_config(Admin):

    def incParamRequest(self, k):
        v = self.request(k)
        if v == '': v = 'off'
        else: v = 'on'
        v = v.upper()
        return v

    def getIncParamMap(self):
        m = {}
        for vari_name in inception_variables.VARIABLES_SORTED:
            m[vari_name] = self.incParamRequest(vari_name)
        return m

    def handle(self):
        incParamMap = self.getIncParamMap()
        inc_db = InceptionDB(host=config('INCEPTION_HOST'), port=config('INCEPTION_PORT', cast=int))
        try:
            incParamMap = inception_variables.reverse_special_variable(incParamMap)
            inc_db.updateVariables(incParamMap)
            #return self.resp()
        except Exception, ex:
            return self.resp(errno=1, errmsg=str(ex))
        pingan_inc_db = InceptionDB(host=config('PINGAN_INCEPTION_HOST'), port=config('PINGAN_INCEPTION_PORT', cast=int))
        try:
            pingan_inc_db.updateVariables(incParamMap)
            return self.resp()
        except Exception, ex:
            return self.resp(errno=1, errmsg=str(ex))