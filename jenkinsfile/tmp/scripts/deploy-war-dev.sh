user="stack"
port="22"
if [ "$setup" = "no" ];then
    echo "setup is no, return"
    exit 0
fi

warName=$1
#开始部署war包到目标服务器
ssh -p $port $user@$setup "cd /usr/bin;./cleanTomcat.sh tomcat-$warName $warName"

# 例子
# src="/var/lib/jenkins/workspace/"$JOB_NAME/POSS/poss-war/target
# 剩余部分动态传入进来
src=/var/lib/jenkins/workspace/$JOB_NAME/$2


scp -P $port "$src/$warName.war" $user@$setup:"/data/tomcat-$warName/webapps/$warName.war"

#start tomcat
ssh -p $port $user@$setup "source /etc/profile;sh /data/tomcat-$warName/bin/startup.sh"
