# -*- coding:utf-8 -*-
import os
import sys
import json
import requests

gitlabSourceRepoSshUrl=sys.argv[1]
project = gitlabSourceRepoSshUrl.split(":")[1].split(".")[0].strip()
service=project.split("/")[1]
branch = sys.argv[2]
json_file="/tmp/{}_{}.json".format(service,branch)

def runBash(bash):
    return_status = os.system(bash)
    print("prepare to run:", bash)
    if return_status != 0:
        print("Some wrong !!!!!!!!!!!!!!!! when doing:" + bash)
        sys.exit(1)

def dockerTag(buildpath, service, version):
    runBash(" docker -H 10.0.100.208:2375 tag ipl/{} registry-vpc.cn-shanghai.aliyuncs.com/ipl/{}:{}".format(buildpath, service, version))

def dockerRmi(buildpath):
    runBash(" docker -H 10.0.100.208:2375 rmi ipl/{}".format(buildpath))

def dockerPush(service, version):
    # this api is not avaliable
    # runBash(" docker -H 10.0.100.208:2375 push registry-vpc.cn-shanghai.aliyuncs.com/ipl/{}:{}".format(service, version))
    url = 'http://10.0.100.208:5678/push'
    data = {
        'image':'registry-vpc.cn-shanghai.aliyuncs.com/ipl/{}:{}'.format(service,version)
    }
    requests.post(url=url,data=json.dumps(data))
    print("steps: push docker image")

def main():
    if os.path.exists(json_file):
        with open(json_file) as fp:
            json_dict = json.load(fp)
            service=json_dict['service']
            version=json_dict['version']
            buildpath=json_dict['buildpath']
            dockerbuild=json_dict['dockerbuild']
    else:
        buildpath=None
        print("these is not tmp json file")
        # sys.exit(1)

    if dockerbuild:
        dockerTag(buildpath, service, version)
        dockerRmi(buildpath)
        dockerPush(service, version)
    else:
        print("no docker image to push")

if __name__ == '__main__':
    main()
