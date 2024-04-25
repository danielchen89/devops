# -*- coding:utf-8 -*-
import requests
from requests.auth import HTTPBasicAuth
import json
import sys
#https://blog.csdn.net/LANNY8588/article/details/103496546?utm_medium=distribute.pc_relevant.none-task-blog-BlogCommendFromMachineLearnPai2-1.control&dist_request_id=49bbd795-329b-454c-8b4e-40f067c4e580&depth_1-utm_source=distribute.pc_relevant.none-task-blog-BlogCommendFromMachineLearnPai2-1.control
#https://www.cnblogs.com/Jame-mei/p/11936934.html

def dingTalkAlert(content,sendgroup):
    headers={'Content-Type': 'application/json'}   #定义数据类型
    # noprod alert group token
    # webhook = 'https://oapi.dingtalk.com/robot/send?access_token=0ad71bced801c8ae3e863e4ff12c757abc162fb22ccede0793462ebfec9bc8bd'
    if sendgroup == "dev":
        webhook = 'https://oapi.dingtalk.com/robot/send?access_token=3124f545b929caddc594b4c88560d1f321cf5536bc248038b9b11e10f52f927a'
    elif sendgroup == "secure":
        webhook = 'https://oapi.dingtalk.com/robot/send?access_token=092ad4c86dbd2d9077cea664ac48c708f0042383cfc198cdbb8c4649fa6b858b'
    elif sendgroup == "bug":
        webhook = 'https://oapi.dingtalk.com/robot/send?access_token=1bff9f4bc02ef0df7716f9fe6999a5497cf82ebb286f19242f618c004c7debea'
    #local test
    elif sendgroup == "test":
        webhook = 'https://oapi.dingtalk.com/robot/send?access_token=f5e60a3a1177133a4fa97078af84699a519350e874223e97212fc48929fa4ddc'
    
    data = {
        "msgtype": "text",
        "text": {"content": content},
        "isAtAll": True}
    res = requests.post(webhook, data=json.dumps(data), headers=headers)   #发送post请求

def sonarqubedingtalk(application_name,gitlab_username,branch):
    token = '64defecb6a2ed85709fdf781981841b981d16b96'
    PARAM = {'component': application_name, 'metricKeys': 'bugs,vulnerabilities,code_smells,coverage,duplicated_lines_density,alert_status'}
    results_url = 'https://sonar.corp.ipaylinks.com/api/measures/component'
    results_response = requests.get(results_url, auth=HTTPBasicAuth(username=token, password=""),params=PARAM)
    results_json = results_response.json()
    results=results_json['component']['measures']

    BugDefineURL="https://sonar.corp.ipaylinks.com/api/issues/search?componentKeys="
    BugDefineParams="&s=FILE_LINE&resolved=false&ps=100&facets=severities%2Ctypes&additionalFields=_all"
    BugDefine_req_url=BugDefineURL+application_name+BugDefineParams
    BugDefine_rsp = requests.get(BugDefine_req_url,auth=HTTPBasicAuth(username=token, password=""))
    BugDefinetext = json.loads(BugDefine_rsp.text)
    facets = BugDefinetext['facets'][0]['values']
    bug = '0'
    leak = '0'
    code_smell = '0'
    coverage = '0'
    density = '0'
    critical_bug_num = '0'
    blocked_bug_num = '0'
    status = ''

    print(facets)
    if results:
        for item in results:
            if item['metric']=="bugs":
                bug=item['value']
            elif item['metric']=="vulnerabilities":
                leak = item['value']
            elif item['metric']=='code_smells':
                code_smell = item['value']
            elif item['metric']=='coverage':
                coverage = item['value']
            elif item['metric']=='duplicated_lines_density':
                density = item['value']
            elif item['metric']=='alert_status':
                status = item['value']
            else:
                pass 
    else:
        print("sonar scan result can not be fetched ")

    if facets:
        for facet in facets:
            if facet['val']=='CRITICAL':
                critical_bug_num = str(facet['count'])
            elif facet['val']=='BLOCKER':
                blocked_bug_num = str(facet['count'])
            else:
                pass

    code_reslut=    "代码扫描统计："+"状态:"+ status + '\n' \
                    "应用负责人:" + gitlab_username + '\n'  \
                    "应用名:" + application_name + '\n'  \
                    "构建版本:" + branch + '\n'  \
                    "Bug数:" + bug + "个，" + '\n' \
                    "漏洞数:" + leak + "个，" + '\n' \
                    "高危漏洞数:" + critical_bug_num + "个，" + '\n' \
                    "阻断漏洞数:" + blocked_bug_num + "个，" + '\n' \
                    "可能存在问题代码："+ code_smell + "行，" + '\n' \
                    "覆盖率:" + coverage + "%，" + '\n' \
                    "重复率:" + density + "%" + '\n' \
                    "静态代码扫描服务发现存在代码安全漏洞，高危以上代码漏洞要求生产部署之前完成修复，请尽快修复再发布项目" + '\n' \
                    "详情请用域控账号登录 https://sonar.corp.ipaylinks.com/dashboard?id={}".format(application_name)

    # if int(bug)>=10 or int(leak)>0:
    #     sendgroup = "dev"
    #     dingTalkAlert(code_reslut, sendgroup)

    # if int(bug)>=10:
    #     sendgroup = "dev"
    #     dingTalkAlert(code_reslut, sendgroup)
    if int(critical_bug_num)>0 or int(blocked_bug_num)>0:
        sendgroup = "bug"
        dingTalkAlert(code_reslut, sendgroup)
