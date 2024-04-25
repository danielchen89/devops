# 不断更新中


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

## jenkinsfile jenkins全自动化打包系统
