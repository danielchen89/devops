#!/usr/bin/python
# -*- coding: utf-8 -*-
import jenkins
import sys

# defaultencoding = 'utf-8'
# reload(sys)
# sys.setdefaultencoding(defaultencoding)

jenkins_server_url = "https://xxxxxxxxxx.com/"
user_id = 'lingyun.chen'
api_token = 'xxxxxxxxxxxxx'
# 实例化jenkins对象，连接远程的jenkins master server
server = jenkins.Jenkins(jenkins_server_url, username=user_id, password=api_token)


lists = ["sensitivedata-eu","sensitivedata-hk","sensitivedata-me","sensitivedata-sg","sensitivedata-uk"]

branch=sys.argv[1]

for service in lists:
    server.build_job('sensitivedata-apps', {'branch': '{}'.format(branch), 'project': 'cloud/{}'.format(service)})