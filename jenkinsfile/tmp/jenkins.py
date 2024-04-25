#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import sys
# defaultencoding = 'utf-8'
# reload(sys)
# sys.setdefaultencoding(defaultencoding)


class BuildClass:
	def __init__(self, project, branch):
		self.project = project;
		self.branch = branch
		self.projectType = ''
		#if branch.find('master')
		# print("project is:", project)

	def isTest(self):
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
			
	def runMavenDeploy(self):
		bash = self.getBaseMavenPath()+ " -Dmaven.javadoc.skip=true -Dmaven.test.skip=true clean deploy  -DaltDeploymentRepository=" + deployType + self.getNexusPath() + deployType
		self.runBash(bash)
		
	def runMavenPackage(self):
		bash = self.getBaseMavenPath()+ " -Dmaven.javadoc.skip=true -Dmaven.test.skip=true clean package"
		self.runBash(bash)

	def runBash(self, bash):
		#os.system(bash)
		print("prepare to run:", bash)
			
	# def notifyOps(self application, branch, state, ossPath):
	def notifyOps(self):
		print("notifyOps")

	def upload2OSS(self, localDir, ossDir):
		#
		print("prepare to upload2OSS:{}, {}" %(localDir, ossDir))


	def buildBaseService(self,deployType):
		self.runBash(self.runMavenDeploy())


	# 构建前端
	def buildFrontendService(self,distParam,buildParam):
		print("buildFrontendService")
		bash = "/bin/bash /data/scripts/deploy-frontend.sh {} {}".format(distParam,buildParam)
		self.runBash(bash)
		self.upload2OSS("", "")
		self.notifyOps()


	#部署后端
	def deployBackendService(self, targetPath):
		print("deployBackendService")
		allfiles = os.listdir(".")
        for file in allfiles:
			if (file.endswith("-facade")):
				print("file path:", file)
				self.runBash("cd " + file);
				self.runMavenDeploy()
				break

	#构建后端buildBackendService项目
	def buildBackendService(self, targetPath):
		print("buildBackendService")
		currentPath = os.getcwd()
		print("currentPath:" + currentPath)
		self.deployBackendService()
		self.runBash("cd " + currentPath);
		self.runMavenPackage()
		self.upload2OSS("", "")
		
	#构建
	def build(self):
		frontProjects = {
						'frontEnd/homesite': ['nodist', 'nobuild'],
						'iPayKjfk/mes-static': ['dist', 'build', ],
						'iPayKjfk/mes-h5-static': ['dist', 'build'],
						'frontEnd/tw-frontend': ['dist', 'build'],
						'iPayDubhe/cashier-front': ['nodist', 'nobuild'],
						'frontEnd/mpsnew': ['dist', 'build'],
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
						}

		tomcatProjects = {
						'iPayKjfk/cfp-poss': 'POSS/poss-war/target',
						'iPayKjfk/cfp-walletservice': 'cfp-walletservice-runner',
						'iPayCore/channel': 'channel-app/target',
						'iPay/commonservice': 'src/commonService_web/target',
						'iPay/notification': 'target',
						'iPayCore/ordercenter': 'ORDERCENTER/fi-ordercenter/target',
						'iPay/poss': 'POSS/poss-war/target',
						'iPay/webgate': 'WEBGATE/fi-webgate/target',
						'iPayCore/txncore': 'TXNCORE/fi-txncore/target',
						}

		if (self.project in frontProjects):
			self.projectType = 'front'
			distParam = frontProjects[self.project][0]
			buildParam = frontProjects[self.project][1]
			self.buildFrontendService(distParam,buildParam)
		elif (self.project in baseProjects):
			self.projectType = 'base'
			deployType = baseProjects[self.project]
			self.buildBaseService(deployType)
		elif (self.project in tomcatProjects):
			self.buildBackendService(self.project[0])
		else:
			print("other backend project")
			self.buildBackendService(None)
			
def main(project,branch):
	bc = BuildClass(project,branch)
	bc.build()

if __name__ == '__main__':
	#gitlabSourceRepoSshUrl = sys.argv[1]
	#project = gitlabSourceRepoSshUrl.split(":")[1].split(".")[0].strip()
	#gitlabTargetBranch = sys.argv[2]
	#main(project,gitlabTargetBranch)
	main('iPayDubhe/cashier-front','master')
	