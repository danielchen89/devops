## aws 
    1)terraform 基础设施即代码 (Infrastructure as Code, IaC) 工具，用于自动化管理和部署云基础架构。
    2）aws-scripts  aws日常运维管理脚本
    3) lambda   lambda脚本

## zabbix
   1)服务端口自动发现，存活状态监控
   2)钉钉告警,电话告警
   3)chatops结合zabbix自动获得服务器监控图

## chatops - 通过聊天的方式完成你的运维工作
        1)  添加域控用户  ldap:add:username:chinesename 如 ldap:add:san.zhang:张三
            启用域控用户  ldap:enable:username
            禁用域控用户  ldap:disable:username 
            删除域控用户  ldap:delete:username  
            查找域控用户  ldap:search:username 
            修改域控密码  ldap:modify:username
        2)  远程服务器操作 (保留功能，生产暂未启用)
            top命令            ssh:hostname:top 如 ssh:prod-unified1:top
            查看磁盘空间大小    ssh:hostname:disk
            查看/data中大文件   ssh:hostname:find
        3)  获取服务器所有监控值  zbx|graph|hostname
            获取服务器监控图      zbx|png|hostname|监控值 如 zbx|png|prod-unified1|CPU usage
        4)  获取具体zk值   zk(1|2):(env|noenv):hostname:具体值  如 zk1:env:dc-front:dc.connect.backup.port
            获取zk节点信息 zk(1|2):(env|noenv):hostname	

## jenkinsfile jenkins全自动化打包系统
    jenkins CI系统（CD需要接入发布系统），解决如下痛点问题：
    1.jenkins打包创建构建job复杂，动作繁琐
    2.同时并发打包能力差
    3.环境问题，打包容易失败
    4.不能随时随地打包，有固定打包时间
    5.前后端打包方式有区别
    6.打包分配权限不规范
    


## svctool.go 服务自动化运维工具

基础综合运维工具（生产版）使用说明
	目前功能及示例：

	启动|停止|重启单个服务并输出日志 : svc start|stop| restart(re) 服务名
	启动|停止|重启所有服务  : svc startall|stopall|restartall 
	查看某个服务的启动状态及端口 : svc status(st) 服务名
	发送某个文件(小于20M)到企业微信 : svc send 文件名
	查看某个服务最近300条日志 : svc log 服务名
	查看某个服务日志的关键字 : svc logr 服务名 关键字
	查看某个服务日志并进行过滤(加双引号) : svc logo 服务名 "过滤命令"
	查看某个服务的错误日志 : svc loge 服务名
	查看某个服务的所有类型的错误日志 : svc logE 服务名 
	查看某个服务的错误日志的10条|50条|200条上下文 : svc loge10|loge50|loge200 服务名 
	查看服务的最新5条|10条错误日志 : svc logen5|logen10 服务名 
	查看本机所有服务的最新5条|10条错误日志 : svc checklogen5|checklogen10
	查看本机所有服务状态 : svc check
	查看本机时间同步配置并更新 : svc checktime
	查看某个服务当前日志大小: svc du 服务名
	动态查看某个服务日志 : svc logf 服务名
	动态查看某个端口或者pid : svc : 端口号或者pid
	查看文件内容过滤无关字符： svc cat 文件名 
	快速查看某个服务的配置文件: svc conf 服务名
	查找根目录下大于100M的文件 : svc find
	查看本机有哪些服务 : svc ls
	查看当前版本 : svc version

## midtool.go 中间件自动化运维工具

基础中间件运维工具（生产版）使用说明
	目前功能及示例：
	目前支持(redis(rds)|haproxy(ha)|kafka(ka))|zookeeper(zk)

	启动|停止单个应用并输出日志 : mid start|stop 应用名
	启动|停止所有应用 : mid startall|stopall
	查看某个应用的启动状态及端口 : mid status(st) 应用名
	查看某个应用最近100条日志 : mid log 应用名
	查看某个应用日志的关键字 : mid logr 应用名 关键字
	查看某个应用success的上下5条日志 : mid logs 应用名
	动态查看某个应用日志 : mid logf 应用名
	发送某个文件(小于20M)到企业微信 : mid send 文件名
	扫描某个组中间件的状态: mid scan 组名
	查看本机所有中间件状态 : mid check
	查看当前版本 : mid version
	特殊的命令：
		查看集群的主节点 : mid master(ma) 应用名 （redis）
		跟随集群某个主节点 : mid replicate(rep) 应用名（redis） 主节点hash
		监控集群某个主节点 : mid monitor 应用名 （redis）
		选举集群的主节点 : mid leader 应用名 （kafka）
		优雅重启服务 : mid reload 应用名(haproxy)
		kafka topic 列出: mid tlist kafka
		kafka topic 操作: mid tdescribe|tcreate|tdelete kafka topic名字
		kafka topic 大小: mid du kafka topic名字
		kafka 获取消息消费情况: mid get kafka topic名字   
		kafka 消费组 列出: mid consumergrouplist(clist) kafka
		kafka 消费组 操作: mid cdescribe kafka 消费组名字

