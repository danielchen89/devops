# -*- coding:utf-8 -*-
import os
import sys
import json
from sonarQubeDingTalk import sonarqubedingtalk

gitlabSourceRepoSshUrl=sys.argv[1]
project = gitlabSourceRepoSshUrl.split(":")[1].split(".")[0].strip()
service=project.split("/")[1]
branch = sys.argv[2]
json_file="/tmp/{}_{}.json".format(service,branch)
gitlabUserName = sys.argv[3].encode('utf-8')
gitlabusername = gitlabUserName.decode('utf-8')

def runBash(bash):
    os.system(bash)

def mainScript(service, version, srcpath, classpath):
    runBash("sonar-scanner \
                -Dsonar.projectKey={0} \
                -Dsonar.projectName={0} \
                -Dsonar.projectVersion={1} \
                -Dsonar.ws.timeout=30 \
                -Dsonar.sources={2}\
                -Dsonar.sourceEncoding=UTF-8 \
                -Dsonar.java.binaries={3} \
                -Dsonar.host.url=https://sonar.corp.ipaylinks.com \
                -Dsonar.login=64defecb6a2ed85709fdf781981841b981d16b96".format(service, version, srcpath, classpath))

def springClassScan(service,version,buildpath,branch):

    if os.path.exists(buildpath):
        #multi moudle
        srcpath=buildpath+"/src"
        classpath=buildpath+"/target/classes"
    else:
        #single moudle
        srcpath="src"
        classpath="target/classes"

    mainScript(service, version, srcpath, classpath)
    sonarqubedingtalk(service,gitlabusername,branch)
    

def tomcatClassScan(service,version,buildpath,branch):

    if buildpath != "":
        srcpath = buildpath + "/src"
        classpath = buildpath + "/target/classes"
    else:
        srcpath = "src"
        classpath = "target/classes"

    mainScript(service, version, srcpath, classpath)
    sonarqubedingtalk(service,gitlabusername,branch)


if os.path.exists(json_file):
    with open(json_file) as fp:
        json_dict = json.load(fp)
        service=json_dict['service']
        version=json_dict['version']
        buildpath=json_dict['buildpath']
        packagetype=json_dict['packagetype']
else:
    buildpath=None
    print("these is not tmp json file")
    # sys.exit(1)

no_scan_list = ['poss','fip-poss','fip-dps'] 

if service not in no_scan_list:
    if buildpath is not None and packagetype=='jar':
        springClassScan(service,version,buildpath,branch)
    elif buildpath is not None and packagetype=='war':
        tomcatClassScan(service,version,buildpath,branch)
    else:
        print("base service build,no need to execute Sonar Scan")
else:
    print("old project or web project,no need to execute Sonar Scan")


