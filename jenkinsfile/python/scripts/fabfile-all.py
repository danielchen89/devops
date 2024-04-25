#!/usr/bin/python3
# encoding=utf-8
from fabric.api import *
import sys

env.roledefs = {
    'dev1': ['root@172.16.4.184'],
    'sit1': ['root@172.16.4.187']
}
env.key_filename = '/root/.ssh/id_rsa'

def get_publish_info(detail):
    l=detail.split()
    l1=[]
    l2=[]
    for i in range(0,len(l)):
        if (i % 2) == 0:
            l1.append(l[i])
        else:
            l2.append(l[i])
    publish_info=dict(zip(l1,l2))

    return publish_info

def deploy_process(detail):
    publish_info=get_publish_info(detail)
    for service,version in publish_info.items():
        print("########## now is deploy service : {} #############".format(service) )
        run("python3 /data/data/scripts/update_deployment.py {0} registry.cn-shanghai.aliyuncs.com/ipl/{0}:{1}".format(service,version))


@roles('dev1')
def dev2_deploy(detail=''):
    deploy_process(detail)
    
@roles('sit1')
def sit1_deploy(detail=''):
    deploy_process(detail)
    # publish_info=get_publish_info(detail)
    # for service,version in publish_info.items():
    #     print("########## now is deploy service : {} #############".format(service) )
    #     run("python3 /data/data/scripts/update_deployment.py {0} registry.cn-shanghai.aliyuncs.com/ipl/{0}:{1}".format(service,version))
