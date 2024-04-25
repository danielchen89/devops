#!/usr/bin/env bash
user="stack"
port="22"
if [ "$setup" = "no" ];then
    echo "setup is no, return"
    exit 0
fi

jarName=$1
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
ssh -p $port $user@$setup "rm -rf /data/$jarName/$jarName.jar"
#复制jar包至测试服务器
scp -P $port "$src/target/$jarName.jar" $user@$setup:"/data/$jarName"

pid=`ssh stack@$setup "ps -ef | grep -w $jarName.jar |grep -v grep| wc -l"`
if [ $pid = 0 ];then
   ssh $user@$setup "/sbin/service $jarName start"
   exit 0
elif [ $pid != 0 ];then
   ssh $user@$setup "ps -ef|grep -w $jarName.jar |grep -v grep|awk '{print \$2}' |xargs kill -9"
   ssh $user@$setup "/sbin/service $jarName start"
fi
