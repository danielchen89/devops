#!/usr/bin/python
# -*- coding: utf-8 -*-
import jenkins
import sys

defaultencoding = 'utf-8'
reload(sys)
sys.setdefaultencoding(defaultencoding)

jenkins_server_url = "http://10.0.100.208:8082"
user_id = 'lingyun.chen'
api_token = '116bc3e2076d5dcdb0ba3b0a9195fa52ec'
# 实例化jenkins对象，连接远程的jenkins master server
server = jenkins.Jenkins(jenkins_server_url, username=user_id, password=api_token)


def createJenkinsJob(service):
    template_xml = "config.xml"
    with open(template_xml) as f:
        profile = f.read()
        JOB_CONFIG = profile
        f.close()
    #
    # service = project.split('/')[1]
    # name = "test-{}".format(service)
    server.create_job(service, JOB_CONFIG)


def help():
    print("""
    用法：
    python createPipeline.py 服务名
        服务名例如 "mop-mapi"
        python createPipeline.py mop-mapi

    """)

if __name__ == '__main__':
     try:
         service=sys.argv[1]
         createJenkinsJob(service)
     except IndexError:
         help()

    # 批量创建项目的方法
    #for item in open("service.txt"):
        #project = item.strip()
        #createJenkinsJob(project)
