# -*- coding:utf-8 -*-
import os
import time

currentPath=os.getcwd()
currentDate=time.strftime("%Y-%m-%d", time.localtime(time.time()))

def runBash(bash):
    os.system(bash)
    print("prepare to run:", bash)

def getFrontendPackage(service,distParam,buildParam,version):
    dst = "/data/package/{}/{}".format(currentDate,version)
    packagePath = "{}/{}.tar.gz".format(dst,service)

    if buildParam == "build":
        runBash("ln -snf /data/node-v8.11.1-linux-x64/bin/* /bin/ && \
                  npm config set registry https://registry.npm.taobao.org && \
                  npm install && \
                  npm run build")
    elif buildParam == "nobuild":
        print("no need to build")

    #清除上次构建产生的临时文件 及 git临时文件
    runBash("rm -rf /tmp/{0} /tmp/{0}.tar.gz && \
               rm -rf {1}/.git*".format(service,currentPath))

    #将目标文件拷贝到/tmp目录下面
    if distParam == "dist":
        srcPath="{}/dist".format(currentPath)
        runBash("cd  /tmp && \
                 mkdir -p {1} && \
                cp -rfp {0} {1}/dist".format(srcPath,service))
    elif distParam == "nodist":
        srcPath= currentPath
        runBash("cp -rfp {} /tmp/{}".format(srcPath,service))

    #将目标文件打包并拷贝到公共存储
    runBash("cd /tmp && \
            tar zcvf {0}.tar.gz {0} && \
            mkdir -p {1} && \
            cp -rfp {0}.tar.gz {1}".format(service,dst))

    return packagePath

def getBackendPackage(service,specialPath,version):
    dst = "/data/package/{}/{}".format(currentDate,version)
    runBash("mkdir -p {}".format(dst))
    #获取war包路径并移动war包到/data/package/目录下
    if specialPath:
        packagePath = "{}/{}.war".format(dst, service)
        srcPath="{}/{}/{}.war".format(currentPath,specialPath,service)
        runBash("cp -rfp {} {}".format(srcPath,dst))
    # 获取jar包路径并移动war包到/data/package/目录下
    else:
        packagePath = "{}/{}.jar".format(dst, service)
        _jarname = "{}.jar".format(service)
        runBash("find  %s -name %s -exec cp {} %s \;" % (currentPath,_jarname,dst))

    return packagePath





