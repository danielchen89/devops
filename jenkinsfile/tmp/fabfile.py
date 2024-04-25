#!/usr/bin/python3
# encoding=utf-8
from fabric.api import *

env.roledefs = {
    'dev1': ['root@172.16.4.184'],
    'sit1': ['root@172.16.4.187']
}
env.key_filename = '/root/.ssh/id_rsa'

@roles('dev1')
def dev1_deploy(service,version):
    run("python3 /data/data/scripts/update_deployment.py {0} registry.cn-shanghai.aliyuncs.com/ipl/{0}:{1}".format(service,version))
