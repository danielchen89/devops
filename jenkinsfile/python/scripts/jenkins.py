# -*- coding: utf-8 -*-
import os
import sys
import time, datetime
import hashlib
import json
# from opsbuild import post_build
from opsbuildaws import post_build_aws
from getPackage import getFrontendPackage, getBackendPackage
from dingtalk import dingTalkAlert
from uploadOss import upload_oss


# defaultencoding = 'utf-8'
# reload(sys)
# sys.setdefaultencoding(defaultencoding)

class BuildClass:
    def __init__(self, project, branch, specialBuildWay):
        self.project = project
        self.branch = branch
        self.specialBuildWay = specialBuildWay
        self.service = self.project.split("/")[1]
        self.timestamps = time.time()
        self.finished_timestamps = int(round(self.timestamps * 1000))
        self.projectType = ''
        self.packageType = ''
        self.dockerbuild = False

    def isTest(self):
        if specialBuildWay == 'dev':
            return False
        else:
            if self.projectType == 'base':
                if self.branch == "master":
                    return True
            if self.branch == "master" or self.branch.find("hotfix") >= 0:
                return True
            else:
                return False

    def getMavenPath(self):
        if self.isTest():
            return "/data/mvn_prod/bin/mvn"
        else:
            return "/data/mvn_dev/bin/mvn"

    def getNexusPath(self):
        if self.isTest():
            return "::default::http://10.0.100.124:8083/nexus/content/repositories/"
        else:
            return "::default::http://10.0.100.124:8081/nexus/content/repositories/"

    def runMavenDeploy(self, deployType):
        bash = self.getMavenPath() + " -Dmaven.javadoc.skip=true -Dmaven.test.skip=true clean deploy  -DaltDeploymentRepository=" + deployType + self.getNexusPath() + deployType
        return bash

    def runMavenPackage(self):
        bash = self.getMavenPath() + " -Dmaven.javadoc.skip=true -Dmaven.test.skip=true clean package"
        self.runBash(bash)

    def runDockerbuild(self):
        bash = self.getMavenPath() + " docker:build"
        return bash

    def runBash(self, bash):
        return_status = os.system(bash)
        print("prepare to run:", bash)
        if return_status != 0:
            print("Some wrong !!!!!!!!!!!!!!!! when doing:" + bash)
            dingTalkAlert(self.branch)
            sys.exit(1)

    def getMd5(self, file_name):
        with open(file_name, 'rb') as fp:
            data = fp.read()
        file_md5 = hashlib.md5(data).hexdigest()
        return file_md5

    def getTimeStamps(self):
        # 时间戳精确到毫秒
        d = datetime.datetime.fromtimestamp(self.finished_timestamps / 1000)
        microtime = d.strftime("%Y%m%d%H%M%S.%f")
        timetext = int(float(microtime) * 1000)
        return timetext

    def generateTagName(self):
        timetext = self.getTimeStamps()
        tagName = "{0}_{1}".format(timetext, self.branch)
        return tagName

    def writeTmpJson(self,buildPath,path,dockerbuild):
        finished_timestamps = self.finished_timestamps
        application_name = self.service
        version = self.version
        branch = self.branch
        if path == None:
            md5 = None
        else:
            md5 = self.getMd5(path)
            remotepath = "publish/" + application_name + "/" + path.split("/")[-2] + "/" + path.split("/")[-1]
        # print("steps: prepare to execute SonarScan")
        json_dict = {"finished_timestamps": finished_timestamps, "project": application_name,
                     "version": version,"branch": branch, "url": path, "md5": md5, 
                      "service": application_name,"buildpath": buildPath, 
                      "packagetype":self.packageType,"dockerbuild":dockerbuild}
        json_str = json.dumps(json_dict)
        writePath = "/tmp/{}_{}.json".format(self.service,self.branch)
        with open(writePath, 'w') as json_file:
            json_file.write(json_str) 

    def buildTag(self):
        tag = self.generateTagName()
        self.runBash("git tag {0} && git push --tags && git checkout -b buildBranch{0} {0}".format(tag))
        return tag

    # 部署后端
    def runBackendSpringServiceMavenDeploy(self):
        print("steps: Deploy Backend Service")
        _deployType = "snapshots"
        allfiles = os.listdir(".")
        for file in allfiles:
            if (file.endswith("-facade")):
                # print("file path:", file)
                cmd = self.runMavenDeploy(_deployType)
                self.runBash("cd {} && {}".format(file, cmd))
                break

    def runBackendSpringServiceDockerBuild(self):
        print("steps: Build Docker Image")
        allfiles = os.listdir(".")
        for file in allfiles:
            if (file.endswith("-web")):
                try:
                    dockerfile_path = file + "/src/main/docker"
                    if os.path.exists(dockerfile_path):
                        cmd = self.runDockerbuild()
                        self.runBash("cd {} && {}".format(file, cmd))
                        return True
                    else:
                        print("docker dir not found, no need to build docker image")
                        return False
                except FileNotFoundError:
                    print("dockerfile not found")
                    return False

            
    def runBackendTomcatServiceMavenDeploy(self, facadePath, deployType):
        if os.path.exists(facadePath):
            cmd = self.runMavenDeploy(deployType)
            self.runBash("cd {} && {}".format(facadePath, cmd))

    #-------------------------以下是主构建函数----------------------------------

    # 构建基础包
    def buildBaseService(self, deployType):
        print("steps: Build Base Service")
        self.runBash(self.runMavenDeploy(deployType))
        self.writeTmpJson(None,None,self.dockerbuild)

    # 构建前端
    def buildFrontendService(self, distParam, buildParam):
        print("steps: Build Frontend Service")
        packagePath = getFrontendPackage(self.service, distParam, buildParam, self.version)
        self.writeTmpJson(None, packagePath,self.dockerbuild)
        # self.notifyOps(_packagePath)

    # 构建后端buildBackendService项目
    def buildBackendTomcatService(self, specialPath, facadePath, deployType,buildPath):
        print("steps: Build Backend Tomcat Service")
        self.runMavenPackage()
        self.runBackendTomcatServiceMavenDeploy(facadePath, deployType)
        packagePath = getBackendPackage(self.service, specialPath, self.version)
        self.writeTmpJson(buildPath,packagePath,self.dockerbuild)
        # self.notifyOps(_packagePath)

    # 构建后端buildBackendService项目
    def buildBackendSpringService(self):
        print("steps: Build Backend Spring Service")
        buildPath = self.service + "-web"
        self.runMavenPackage()
        self.runBackendSpringServiceMavenDeploy()
        dockerbuild = self.runBackendSpringServiceDockerBuild()
        packagePath = getBackendPackage(self.service, None, self.version)
        self.writeTmpJson(buildPath,packagePath,dockerbuild)
        # self.notifyOps(_packagePath)

    # 构建
    def build(self):
        frontProjects = {
            'frontEnd/homesite': ['nodist', 'nobuild'],
            'iPayKjfk/mes-static': ['dist', 'build', ],
            'iPayKjfk/mes-h5-static': ['dist', 'build'],
            'frontEnd/tw-frontend': ['dist', 'build'],
            'iPayDubhe/cashier-front': ['nodist', 'nobuild'],
            'frontEnd/mpsnew': ['dist', 'nobuild'],
            'frontEnd/op-static': ['dist', 'build'],
            'frontEnd/mp-static': ['dist', 'build'],
            'frontEnd/nmp-static': ['dist', 'build'],
            'frontEnd/ticket-static': ['dist', 'build'],
            'frontEnd/risk-static': ['dist', 'build'],
            'ops/op-dashboard-static': ['dist', 'build'],
            'da/finereport': ['nodist', 'nobuild'],
            'iPayLinks-BCS/omnidb': ['nodist', 'nobuild'],
            'pep/pep-frontend': ['dist', 'build'],
            'frontEnd/ipaylinks': ['nodist', 'nobuild'],
        }

        baseProjects = {
            'iPay/Ipaycommon': 'snapshots',
            'iPayDubhe/ipaylinks-base': 'releases',
            'basic-services/ipaylinks-base-archetype': 'snapshots',
            'basic-services/ipaylinks-base-parent': 'snapshots',
            'IPLCommon/common': 'snapshots',
            'iPayLinks/spring-ipaylinks-root': 'releases',
            'iPayChannelFront/front-base': 'snapshots',
            'iPayMerak/cmp-css-common-framework': 'snapshots',
            'iPayKjfk/cfp-common-utils': 'snapshots',
            'iPayDubhe/file-oss': 'releases',
            'basic-services/base-cloud-parent': 'snapshots',
            'basic-services/base-cloud-gateway-archetype': 'snapshots',
            'basic-services/base-cloud-archetype': 'snapshots',
            'cloud/cloud-common': 'snapshots',
            'IPLRiskCenter/bigdata-base': 'snapshots',
            'IPLRiskCenter/IPLRulePlugin': 'snapshots',
            'cloud/cloud-swimlane-router-starter': 'snapshots',
            'cloud/sensitivedata-common': 'snapshots',
        }

        tomcatProjects = {
            'iPayKjfk/cfp-poss': ['POSS/poss-war/target', '', ''],
            'iPayCore/channel': ['channel-app/target', 'channel-stub', 'releases'],
            'iPay/commonservice': ['commonService_web/target', 'commonService_stub', 'snapshots'],
            'iPay/notification': ['target', '', ''],
            'iPayCore/ordercenter': ['ORDERCENTER/fi-ordercenter/target', 'ordercenter_stub', 'snapshots'],
            'iPay/poss': ['POSS/poss-war/target', '', ''],
            'iPay/webgate': ['WEBGATE/fi-webgate/target', '', ''],
            'iPayCore/txncore': ['TXNCORE/fi-txncore/target', 'TXNCORE/txncore-facade', 'snapshots'],
            'iPayCore/accounting': ['ACCOUNTING/fi-accounting/target', 'ACCOUNTING/accounting-facade', 'snapshots'],
            'iPay/if-task': ['target', '', ''],
            'IPLRiskCenter/bigdata-ws': ['target', '', ''],
            'IPLRiskCenter/bigdata-admin': ['target', '', ''],
            'iPayChannelFront/molpay': ['target', '', ''],
        }

        self.version = self.buildTag()
        if (self.project in frontProjects):
            self.projectType = 'front'
            self.packageType = 'tar.gz'
            distParam = frontProjects[self.project][0]
            buildParam = frontProjects[self.project][1]
            self.buildFrontendService(distParam, buildParam)
        elif (self.project in baseProjects):
            self.projectType = 'base'
            deployType = baseProjects[self.project]
            self.buildBaseService(deployType)
        elif (self.project in tomcatProjects):
            specialPath = tomcatProjects[self.project][0]
            facadePath = tomcatProjects[self.project][1]
            deployType = tomcatProjects[self.project][2]
            buildPath = specialPath.replace("/target","").replace("target","")
            self.packageType = 'war'
            self.buildBackendTomcatService(specialPath, facadePath, deployType,buildPath)
            # self.writeTmpJson(buildPath)

        else:
            # buildPath = self.service + "-web"
            self.packageType = 'jar'
            self.buildBackendSpringService()
            # self.writeTmpJson(buildPath)

def main(project, branch, specialBuildWay):
    bc = BuildClass(project, branch, specialBuildWay)
    bc.build()

if __name__ == '__main__':
    gitlabSourceRepoSshUrl = sys.argv[1]
    project = gitlabSourceRepoSshUrl.split(":")[1].split(".")[0].strip()
    gitlabTargetBranch = sys.argv[2]
    specialBuildWay = None
    if len(sys.argv) >= 4:
        specialBuildWay = sys.argv[3]
    main(project, gitlabTargetBranch, specialBuildWay)
