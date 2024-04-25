#!/usr/bin/env bash
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

jarName=$1

#开始备份jar包
srctest="/var/lib/jenkins/workspace/"$JOB_NAME
dst="/data/package/$version"
mkdir -p $dst
find $srctest -name "$1.jar" -exec cp {} $dst \;
echo "jar包备份至nginx完毕"


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


if [[ $2 == "" ]]
then
    src=/var/lib/jenkins/workspace/$JOB_NAME/$jarName-web
elif [[ $2 == "no" ]]
then
    src=/var/lib/jenkins/workspace/$JOB_NAME
else
    src=/var/lib/jenkins/workspace/$JOB_NAME/$2
fi

#登录远程服务器执行删除jar包命令
ssh -p $port stack@$setup "rm -rf /data/$jarName/$jarName.jar"
#复制jar包至测试服务器
scp -P $port "$src/target/$jarName.jar" $user@$setup:"/data/$jarName"

pid=`ssh stack@$setup "ps -ef | grep -w $jarName.jar |grep -v grep| wc -l"`
if [ $pid = 0 ];then
   ssh stack@$setup "/sbin/service $jarName start"
   exit 0
elif [ $pid != 0 ];then
   ssh stack@$setup "ps -ef|grep -w $jarName.jar |grep -v grep|awk '{print \$2}' |xargs kill -9"
   ssh stack@$setup "/sbin/service $jarName start"
fi