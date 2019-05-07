#coding=utf-8

import sys
sys.path.append('../')
from common import *
from model.department_model import DepartmentModel
from model.mysql_server_model import MysqlServerModel
from model.dept_server_model import DeptServerModel

class index(Admin):
    def handle(self):
        dept_id = self.request('dept_id')
        departModel = DepartmentModel()
        deptServerModel = DeptServerModel()
        tmp_list = departModel.rows()
        dept_list = []
        for tmp in tmp_list:
            if tmp['en_name'] != 'all-user' and tmp['en_name'] != 'developer':
                dept_list.append(tmp)
        if dept_id == '':
            if len(dept_list) == 0:
                has_select_list = []
                rest_server_list = []
            else:
                dept_id = dept_list[0]['id'] 
        else:
            self.safeId(dept_id)
        has_select_list, rest_server_list = deptServerModel.getServerByDeptId(dept_id)
        print has_select_list, rest_server_list
        self.data['dept_id'] = dept_id
        self.data['depart_list'] = dept_list
        self.data['has_select_list'] = has_select_list
        self.data['rest_server_list'] = rest_server_list
        return self.render().permission_index(data=self.data)

class commit(Admin):
    def handle(self):
        sel_ips = self.request('sel_ips')
        #print sel_ips
        dept_id = self.request('dept_id')
        self.safeId(dept_id)
        sel_ip_list = sel_ips.split(',')
        sel_ip_list = [ item.split('/')[0] for item in sel_ip_list ]
        #print sel_ip_list
        #assert 0
        sel_ip_list = list(set(sel_ip_list))
        serverModel = MysqlServerModel()
        dst_server_list = serverModel.loadServerByIpList(sel_ip_list)
        dst_server_id_list = [ dst_server['id'] for dst_server in dst_server_list ]
        deptServerModel = DeptServerModel()
        src_server_list, _ = deptServerModel.getServerByDeptId(dept_id)
        src_server_id_list = [src_server['id'] for src_server in src_server_list]
        to_add, to_del = self.diffServerIdList(src_server_id_list, dst_server_id_list)
        if len(to_add) > 0:
            #add
            deptServerModel.addDeptIdServerIds(dept_id, to_add)
        if len(to_del) > 0:
            #del
            deptServerModel.delDeptIdServerIds(dept_id, to_del)
        return self.resp()

    def diffServerIdList(self, src_server_id_list, dst_server_id_list):
        to_add = []
        to_del = []
        for id in src_server_id_list:
            if id not in dst_server_id_list:
                to_del.append(id)
        for id in dst_server_id_list:
            if id not in src_server_id_list:
                to_add.append(id)
        return to_add, to_del