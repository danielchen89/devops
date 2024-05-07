# -*- coding: utf-8 -*-

import time
import hashlib
import urllib
import random
import string
import requests
from collections import OrderedDict, defaultdict
import xmltodict
import sys
import json
import os
requests.packages.urllib3.disable_warnings()


class HTTP_CHECK(object):
    """docstring for HTTP_CHECK"""

    def __init__(self):
        super(HTTP_CHECK, self).__init__()
        self.data_dir = '/etc/zabbix/scripts/services_check/services.txt'
        self.send_data = '/etc/zabbix/scripts/services_check/.data'
        self.zabbix_server = '47.254.71.255'

    def random_str(self):
        ret = ''.join(random.sample(string.ascii_letters + string.digits, 8))
        return ret

    def write_data(self, data):
        with open(self.send_data, 'a') as f:
            f.write(data)

    def sort_dict(self, arg):

        _dict = OrderedDict()
        items = sorted(arg.keys())
        for i in items:
            _dict[i] = arg[i]
        return _dict

    def dict_form(self, arg):

        _list = []
        for k, v in arg.items():
            _list.append('&{0}={1}'.format(k, v))
        _list[0] = _list[0].replace('&', '')
        return ('').join(_list)

    def create_port(self):
        # 初始化一个列表，如果有未定义的key不会报错
        data = defaultdict(list)
        with open(self.data_dir, 'r') as f:
            for line in f.readlines():
                ret = line.strip('\n').split(',')
                _d = {'{#SERVICENAME}': ret[0], '{#SERVICEIP}': ret[1], '{#SERVICEPORT}': ret[2]}
                data['data'].append(_d)
        # for k, v in sites.items():
        #     data['data'].append({'{#CHANNELNAME}': k, '{#CHANNELSTATUS}': '{0}'.format(k),
        #                          '{#CHANNELTIMECONSUMING}': '{0}'.format(k)})
        print(json.dumps(data))
    
    def create_url(self):

        data = defaultdict(list)
        with open(self.data_dir, 'r') as f:
            for line in f.readlines():
                ret = line.strip('\n').split(',')
                if ret[3] !='':
                    _d = {'{#SERVICENAME}': ret[0]}
                    data['data'].append(_d)
        print(json.dumps(data))
    def nowtime(self):
        return lambda:int(round(time.time() * 1000))

    def send_get(self, url):

        ret = {'status': 'success', 'timeconsuming': 0}
        try:
            start = time.clock()
            r = requests.get(url,timeout=3)
            _data = json.loads(r.text)
            request_time = round((time.clock() - start) * 1000,2)
            if not r.status_code == 200 or not _data['status'] == 'UP':
                ret['status'] = _data
            ret['timeconsuming'] = request_time
        except Exception as e:
            ret['status'] = str(e)
        return ret

    def zbx_sender(self):

        ret = True
        try:
            os.system('/bin/bash -c "zabbix_sender -z {0} -i {1} &>/dev/null"'.format(self.zabbix_server, self.send_data))
        except:
            ret = False
        return ret
    def get_sites_data(self):

	_data = []
        with open(self.data_dir,'r') as f:
            for line in f.readlines():
                ret = line.strip('\n').split(',')
                if ret[3] !='':
                #url = 'http://{0}:{1}/health'.format(ret[1], ret[2])
                    _data.append((ret[0],ret[3]))
        return _data

    def get_data(self, ip):

        if os.path.exists(self.send_data):
            os.remove(self.send_data)
        for i in self.get_sites_data():
            ret = self.send_get(i[1])
            data = '{0}  http_check_status[{1}] {2}\n{3}  http_check_timeconsuming[{4}]  {5}\n'.format(ip,i[0],ret['status'],ip,i[0],ret['timeconsuming'])
            self.write_data(data)

    def main_run(self, ip):

        try:
            self.get_data(ip)
            self.zbx_sender()
            print(int(1))
        except Exception as e:
            print(int(0))


if __name__ == '__main__':

    ins = HTTP_CHECK()
    if sys.argv[1] == 'portlist':
       ins.create_port()
    elif sys.argv[1] == 'urllist':
       ins.create_url()
    elif sys.argv[1] == 'healthdata':
         ins.main_run(sys.argv[2])


