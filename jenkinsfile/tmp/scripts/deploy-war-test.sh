#!/bin/bash

if [ "$version" == "" ];then
    version=$(/usr/bin/python /data/mvn_prod/conf/updateVersion.py)
    echo "version from version.txt is $version"
else
    /usr/bin/python /data/mvn_prod/conf/updateVersion.py $version
fi

tag="testbuild_tag_version_$version"
git tag $tag
git push --tags
git checkout -b buildBranch$tag $tag

warName=$1
#开始备份war包
srctest="/var/lib/jenkins/workspace/"$JOB_NAME
dst="/data/package/$version"
mkdir -p $dst
find $srctest -name "$1.war" -exec cp {} $dst \;
echo "WAR包备份至nginx完毕"

#上传包到OSS
jar_path=${dst}'/'$jarName'.jar'
url='http://139.196.102.177:444/package/'${version}'/'${jarName}'.jar'
md5=$(md5sum $jar_path |cut -d ' ' -f1)
python /data/scripts/build.py -p $jarName -v $version -u $url -m $md5


user="stack"
port="22"
if [ "$setup" = "no" ];then
    echo "setup is no, return"
    exit 0
fi

warName=$1
#开始部署war包到目标服务器
ssh -p $port stack@$setup "cd /usr/bin;./cleanTomcat.sh tomcat-$warName $warName"

# 例子
# src="/var/lib/jenkins/workspace/"$JOB_NAME/POSS/poss-war/target
# 剩余部分动态传入进来
src=/var/lib/jenkins/workspace/$JOB_NAME/$2


scp -P $port "$src/$warName.war" stack@$setup:"/data/tomcat-$warName/webapps/$warName.war"

#start tomcat
ssh -p $port stack@$setup "source /etc/profile;sh /data/tomcat-$warName/bin/startup.sh"