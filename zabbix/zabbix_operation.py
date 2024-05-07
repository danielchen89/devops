#!/usr/bin/env python
# -*- coding:utf8 -*-

import requests
import json
import sys

"""
    官方文档地址：
    https://www.zabbix.com/documentation/3.4/zh/manual/api
    https://www.zabbix.com/documentation/5.0/manual/api
"""

class ZabbixApi:
    def __init__(self):
        # self.address = 'http://172.168.1.243:8000'
        # self.url = self.address + '/api_jsonrpc.php'
        # self.username = 'Admin'
        # self.password = 'zabbix'    
        self.address = 'https://zbx.corp.ipaylinks.com/'
        self.url = self.address + '/api_jsonrpc.php'
        self.username = 'chatops'
        self.password = '@0MIucG2xF'    
        self.headers = {'content-type': 'application/json',}
        self.auth=self.login()

    def login(self):
        data = {
            "jsonrpc": "2.0",
            "method": "user.login",
            "params": {
                'user': self.username,
                'password': self.password,
            },
            "auth": None,
            "id": 1,
        }

        request = requests.post(url=self.url, headers=self.headers,data=json.dumps(data))
        content = json.loads(request.text)
        request.close()
        return content

    def hostGet(self):
        data = {
            "jsonrpc": "2.0",
            "method": "host.get",
            "params": {
                'output': [
                    'hostid',
                    'name'],
                'selectInterfaces': [
                    "interfaceid",
                    "ip"
                ]
            },
            "auth": self.auth['result'],
            "id": 2,
        }

        request = requests.post(url=self.url, headers=self.headers,data=json.dumps(data))
        content = json.loads(request.text)
        request.close()
        # return content
        #将host查询结果写入字典
        dict = {}
        for host in content['result']:
            dict[host['name']] = host['hostid']
        return dict

    def graphGet(self,hostid):
        data = {
            "jsonrpc": "2.0",
            "method": "graph.get",
            "params": {
                "output": "extend",
                "hostids": hostid,
                "sortfield": "name"
            },
            "auth": self.auth['result'],
            "id": 1
        }

        request = requests.post(url=self.url, headers=self.headers,data=json.dumps(data))
        content = json.loads(request.text)
        request.close()
        #将图片查询结果写入字典
        dict = {}
        for graph in content['result']:
            dict[graph['name']] = graph['graphid']    
        return dict

    def itemGet(self,hostid):
        data = {
            "jsonrpc": "2.0",
            "method": "item.get",
            "params": {
                "output": "extend",
                "hostids": hostid,
                "search": {
                    "key_": "system"
                },
                "sortfield": "name"
            },
            "auth": self.auth['result'],
            "id": 1
        }

        request = requests.post(url=self.url, headers=self.headers,data=json.dumps(data))
        content = json.loads(request.text)
        request.close()
        # return content['result']
        dict = {}
        for item in content['result']:
            #项目名，项目id
            dict[item['name']] = item['itemid']    
        return dict

    def graphItemGet(self,graphid):
        data = {
            "jsonrpc": "2.0",
            "method": "graphitem.get",
            "params": {
                "output": "extend",
                "graphids": graphid
            },
            "auth": self.auth['result'],
            "id": 1
        }

        request = requests.post(url=self.url, headers=self.headers,data=json.dumps(data))
        content = json.loads(request.text)
        request.close()
        graphids = []
        for graphitem in content['result']:
            #项目名，项目id
            graphids.append(graphitem["graphid"])
        graphids = list(set(graphids))
        graphids.sort()
        return graphids

    def getPng(self,graphid):
        header = {
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Cookie": "PHPSESSID=2bvctu9rva99ppd74gaopb8i42; zbx_sessionid=" + self.auth['result'],
            "Pragma": "no-cache",
            "Upgrade-Insecure-Requests": "1"
        }

        #http://172.168.1.243:8000/chart2.php?graphid=1395&period=3600&width=900
        charUrl = self.address + "/chart2.php?graphid=" + str(graphid) + "&period=3600&width=900"
        resp = requests.get(charUrl, headers=header)
        pngPath = "/tmp/"+ str(graphid) +".png"
        with open(pngPath, 'wb') as f:
            f.write(resp.content)
        f.close()
        return pngPath


def zabbixMain(operation,hostname,monitorkey=None,graphid=None,hostid=None):
    
    zbx=ZabbixApi()
    hosts=zbx.hostGet()
    graphs=zbx.graphGet(hostid=hosts[hostname])
    if operation == "host":
        return hosts
    if operation == "graph":
        return tuple(graphs.keys())
    if operation == "png":
        pngPath=zbx.getPng(graphid=graphs[monitorkey])
        return pngPath
    if operation == "item":
        items=zbx.itemGet(hostid)
        return items
    if operation == "graphitem":
        graphitems=zbx.graphItemGet(graphid)
        return graphitems

if __name__ == '__main__':
    hostname="zabbixserver"
    if len(sys.argv) < 2:
        print("参数必须大于1个")
        sys.exit()
    else:
        operation=sys.argv[1]
        # hostname=sys.argv[2]
    if operation == "png":
        monitorkey=sys.argv[2]
        result=zabbixMain(operation,hostname,monitorkey)
    if operation == "graph":
        result=zabbixMain(operation,hostname,monitorkey=None)
    if operation == "item":
        hostid=sys.argv[2] 
        result=zabbixMain(operation,hostname,hostid)
    if operation == "graphitem":
        graphid=sys.argv[2] 
        result=zabbixMain(operation,hostname,graphid)

    print(result)


