#!/usr/bin/env bash

if [[ $2 == "dist" ]]
then
    src_dir="/var/lib/jenkins/workspace/${JOB_NAME}/dist"
elif [[ $2 == "nodist" ]]
then
    src_dir="/var/lib/jenkins/workspace/${JOB_NAME}"
fi


if [[ $3 == "build" ]]
then
    ln -snf /data/node-v8.11.1-linux-x64/bin/* /bin/
	npm config set registry https://registry.npm.taobao.org
    npm install
    npm run build
elif [[ $3 == "nobuild" ]]
then
    echo "no need to build"
fi


user="stack"
#env=$(/bin/echo $setup | cut -d '-' -f1)
#first_dir=/data/frontcodes/$env
first_dir=/data/frontcodes/dev1
last_dir=$1

#清除上次构建产生的临时文件 及 git临时文件
#rm -rf /tmp/$last_dir /tmp/$last_dir.zip
rm -rf /tmp/$last_dir /tmp/$last_dir.tar.gz
rm -rf /var/lib/jenkins/workspace/${JOB_NAME}/.git*

#进入临时目录，拷贝文件到远程目录
cd /tmp

if [[ $2 == "dist" ]]
then
    mkdir $last_dir
    cp -rfp $src_dir $last_dir/dist
elif [[ $2 == "nodist" ]]
then
    cp -rfp $src_dir $last_dir
fi

#zip -r $last_dir.zip $last_dir
#scp $last_dir.zip $user@$setup:/tmp
#ssh $user@$setup "unzip -o /tmp/$last_dir.zip  -d $first_dir"

tar zcvf $last_dir.tar.gz $last_dir
scp $last_dir.tar.gz $user@$setup:/tmp
ssh $user@$setup "tar zxvf /tmp/$last_dir.tar.gz  -C $first_dir"