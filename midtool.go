// 基础服务器运维操作工具

package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"net"
	"net/http"
	"os"
	"os/exec"
	"strings"
	"syscall"
	"time"

	"github.com/hpcloud/tail"
)

var err string
var action, argname, service, keyword, servicetype, output string
var _cmd, _cmd1, _cmd2, pid string
var logname, logfile, realdir string
var dirs []string

//获取当前时间戳作为版本号，精确到分
var version string = "20231229.1030"
var help_content string = `
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
`

// 判断文件或者文件夹是否存在
func Exists(path string) bool {
	_, err := os.Stat(path) //os.Stat获取文件信息
	if err != nil {
		if os.IsExist(err) {
			return true
		}
		return false
	}
	return true
}

//查看当前服务状态
//增加一个判断，如果服务没启动，迅速pass不执行接下来的命令
func serviceStatus(service string) {
	fmt.Println("现在查看" + service + "服务运行状态...\n")
	if service == "redis" {
		output = runLinuxCmdWithPureReturn("pgrep -f redis-server")
		if len(strings.TrimSpace(string(output))) > 0 {
			_cmd = fmt.Sprintf("redis-cli --cluster check 127.0.0.1:6380")
		}
	} else if service == "haproxy" {
		output = runLinuxCmdWithPureReturn("pgrep -f haproxy")
		if len(strings.TrimSpace(string(output))) > 0 {
			_cmd = fmt.Sprintf("/usr/local/haproxy/sbin/haproxy -f /usr/local/haproxy/etc/haproxy.cfg -c")
		}
	} else if service == "nginx" {
		output = runLinuxCmdWithPureReturn("pgrep -f nginx")
		if len(strings.TrimSpace(string(output))) > 0 {
			_cmd = fmt.Sprintf("/usr/local/nginx/sbin/nginx -t")
		}
	} else if service == "kafka" {
		output = runLinuxCmdWithPureReturn("pgrep -f  kafkaServer")
		if len(strings.TrimSpace(string(output))) > 0 {
			_cmd = fmt.Sprintf("cd %s && ./bin/kafka-topics.sh --bootstrap-server %s:9092   --describe", findRealDir(service), getPrivateIpAddress())
		}
	} else if service == "zookeeper" {
		output = runLinuxCmdWithPureReturn("pgrep -f  zookeeper")
		if len(strings.TrimSpace(string(output))) > 0 {
			_cmd = fmt.Sprintf("source /etc/profile && cd %s && ./bin/zkServer.sh status", findRealDir(service))
		}

	}
	runLinuxCmd(_cmd)
	_cmd = fmt.Sprintf("ps -ef | grep -w %s | grep -v grep | grep -v -w mid", service)
	runLinuxCmd(_cmd)
}

func scanEndpoint(group string) {
	fmt.Println("现在扫描" + group + "组的服务端口...\n")
	var url string
	url = fmt.Sprintf("http://endpoint.yjbyw.gj:6666/view/%s", group)
	resp, err := http.Get(url)
	if err != nil {
		fmt.Printf("Error fetching %s: %v\n", url, err)
		return
	}
	defer resp.Body.Close()
	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		fmt.Printf("Error reading response body: %v\n", err)
		return
	}
	var data map[string][]string
	if err := json.Unmarshal(body, &data); err != nil {
		fmt.Printf("Error parsing response body: %v\n", err)
		return
	}
	for _, address := range data[group] {
		parts := strings.Split(address, " ")
		if len(parts) != 2 {
			fmt.Println("Invalid address:", address)
			continue
		}

		cmd := exec.Command("nc", "-w", "10", "-z", parts[0], parts[1])
		if err := cmd.Run(); err != nil {
			fmt.Println(address, "fail")
		} else {
			fmt.Println(address, "ok")
		}
	}
}

///////////////////////////////////////特殊的命令start///////////////////////////////////////
//查看当前服务主节点
func serviceMaster(service string) {
	fmt.Println("现在查看" + service + "集群的主节点...\n")
	if service == "redis" {
		// _cmd = fmt.Sprintf("redis-cli -p 6380 cluster nodes  | grep master")
		_cmd = `
			#!/bin/bash
			redis-cli -p 6380 cluster nodes
			printf '%.0s-' {1..100}; echo
			for master_id in $(redis-cli -p 6380 cluster nodes | grep master | grep -v fail | grep -v grep| awk '{print $1}')
			do
				master_ip=$(redis-cli -p 6380 cluster nodes | grep $master_id | grep master | grep -v fail | grep -v grep |awk '{print $2}' | awk -F ':' '{print $1}')
				echo "Master ip: $master_ip, master id: $master_id"
				redis-cli -p 6380 cluster nodes | grep $master_id | grep -v fail | grep -v grep |awk '{print $2}' | awk -F ':' '{print $1}'
			done
		`
	}
	runLinuxCmd(_cmd)

}

func serviceMonitor(service string) {
	fmt.Println("现在监控" + service + "的连接情况...\n")
	if service == "redis" {
		_cmd = fmt.Sprintf("redis-cli -p 6380 monitor | grep -Ev 'PUBLISH|PING|INFO|REPLCONF|AUTH'")
	}
	runLinuxCmd(_cmd)

}

//重新跟随主节点
func serviceReplicate(service string, masterhash string) {
	fmt.Println("现在redis重新跟随主节点" + masterhash + "...\n")
	if service == "redis" {
		_cmd = fmt.Sprintf("redis-cli  -p 6380 cluster replicate %s", masterhash)
	}
	runLinuxCmd(_cmd)

}

func serviceLeader(service string) {
	if service == "kafka" {
		fmt.Println("现在kafka重新分配partition的leader...\n")
		_cmd = fmt.Sprintf("cd %s && ./bin/kafka-leader-election.sh --bootstrap-server %s:9092 --all-topic-partitions --election-type PREFERRED", findRealDir(service), getPrivateIpAddress())
	}
	runLinuxCmd(_cmd)

}

//重启的命令
func serviceReload(service string) {
	serviceStatus(service)
	time.Sleep(3 * time.Second)
	fmt.Println("--------------------正在reload" + service + "服务-------------------")
	if service == "haproxy" {
		_cmd = fmt.Sprintf("/usr/local/haproxy/sbin/haproxy -f /usr/local/haproxy/etc/haproxy.cfg -sf %s", getPid(service))
		runLinuxCmd(_cmd)
	}

	time.Sleep(3 * time.Second)
	fmt.Println("--------------------现在查看服务" + service + "日志-------------------")
	tailfServiceLog(service)
}

//检查/opt/app下面所有服务的状态，nginx.kafka,redis等的服务状态
func checkMiddlewareService() {

	fmt.Println("#########判断中间件的状态##########")
	//判断rpm安装的中间件服务的状态
	for _, middlewareservice := range []string{
		"nginx", "keepalived", "haproxy", "consul", "zabbix", "filebeat",
		"elasticsearch", "logstash", "kibana", "redis-server", "redis-sentinel"} {
		_cmd = fmt.Sprintf("whereis %s | awk -F ':' '{print $2}' | grep -v ^$", middlewareservice)
		_cmd = runLinuxCmdWithPureReturn(_cmd)
		// fmt.Println("第一次执行" + _cmd)
		if _cmd != "" {
			_cmd = fmt.Sprintf("ps -ef | grep %s | grep -v grep", middlewareservice)
			_cmd = runLinuxCmdWithPureReturn(_cmd)
			// fmt.Println("第二次执行" + _cmd)
			if _cmd != "" {
				fmt.Println(middlewareservice + " 服务启动 Success")
			} else {
				fmt.Println(middlewareservice + " 服务启动 Fail!!!")
			}
			// } else {
			// 	fmt.Println(middlewareservice + " 服务不存在")
		}
	}

	//判断tar.gz安装的中间件服务状态
	for _, middlewareservice := range []string{"zookeeper*", "kafka*"} {
		_cmd = fmt.Sprintf("ls -d  /opt/app/%s 2>/dev/null", middlewareservice)
		_cmd = runLinuxCmdWithPureReturn(_cmd)
		// fmt.Println("第一次执行" + _cmd)
		if _cmd != "" {
			_cmd = fmt.Sprintf("ps -ef | grep '/opt/app/%s' | grep -v grep", middlewareservice)
			_cmd = runLinuxCmdWithPureReturn(_cmd)
			// fmt.Println("第二次执行" + _cmd)
			if _cmd != "" {
				fmt.Println(middlewareservice + " 服务启动 Success")
			} else {
				fmt.Println(middlewareservice + " 服务启动 Fail!!!")
			}

		}
	}

	for _, middlewareservice := range []string{"redis_exporter", "kafka_exporter"} {
		_cmd = fmt.Sprintf("ls -d  /opt/app/%s 2>/dev/null", middlewareservice)
		_cmd = runLinuxCmdWithPureReturn(_cmd)
		// fmt.Println("第一次执行" + _cmd)
		if _cmd != "" {
			_cmd = fmt.Sprintf("ps -ef | grep '%s' | grep -v grep", middlewareservice)
			_cmd = runLinuxCmdWithPureReturn(_cmd)
			// fmt.Println("第二次执行" + _cmd)
			if _cmd != "" {
				fmt.Println(middlewareservice + " 服务启动 Success")
			} else {
				fmt.Println(middlewareservice + " 服务启动 Fail!!!")
			}

		}
	}

	fmt.Println("#########判断时间是否正确##########")
	fmt.Println("当前时间： " + time.Now().Format("2006-01-02 15:04:05"))
	//判断是否仿真dns连仿真的，79的dns连79的，70的dns连70的
	fmt.Println("#########查看/etc/resolv.conf是否正确##########")
	_cmd = fmt.Sprintf("cat /etc/resolv.conf | grep -v ^# | grep -E '172.28.62.69|172.28.62.70|192.168.179.225|192.168.179.226|192.168.171.95|192.168.171.96|192.168.171.188|192.168.76.182|192.168.76.183|172.16.35.54|172.16.35.55|172.16.29.86|172.16.29.87|197.1.14.83|197.1.14.84'| wc -l")
	_cmd = runLinuxCmdWithPureReturn(_cmd)
	// fmt.Println("第一次执行" + _cmd)
	if _cmd == "2" {
		fmt.Println("/etc/resolv.conf 配置正确")
	} else {
		fmt.Println("/etc/resolv.conf 配置不正确，请检查！！！")
	}

}

///////////////////////////////////////特殊的命令end///////////////////////////////////////

func getDirList(path string) {
	fs, _ := ioutil.ReadDir(path)
	for _, file := range fs {
		if file.IsDir() {
			_dir := path + file.Name()
			// /opt/app下的所有目录汇集在这
			dirs = append(dirs, _dir)
		}
	}
}

//consul服务启动

func kafkaExporterStart() {
	_cmd = fmt.Sprintf("source /etc/profile && cd /opt/app/kafka_exporter && nohup ./kafka_exporter --kafka.server=%s:9092 > nohup.out 2>&1 &", getPrivateIpAddress())
	cmd := exec.Command("sh", "-c", _cmd)
	fmt.Println(_cmd)

	// 设置命令执行的工作目录
	cmd.Dir = "/opt/app/kafka_exporter"

	// 将命令的输出重定向到标准输出
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	// 执行命令
	err := cmd.Run()
	if err != nil {
		log.Fatal(err)
	}
	fmt.Println("kafka_exporter服务启动Success")
}

func redisExporterStart() {
	_cmd = fmt.Sprintf("source /etc/profile && cd /opt/app/redis_exporter && nohup ./redis_exporter  -redis.addr %s -redis.password 'F6x7uVBNovIl1Z@J' -web.listen-address ':9121' > nohup.out 2>&1 &", getPrivateIpAddress())
	cmd := exec.Command("sh", "-c", _cmd)
	fmt.Println(_cmd)

	// 设置命令执行的工作目录
	cmd.Dir = "/opt/app/redis_exporter"

	// 将命令的输出重定向到标准输出
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	// 执行命令
	err := cmd.Run()
	if err != nil {
		log.Fatal(err)
	}
	fmt.Println("redis_exporter服务启动Success")
}

//启动所有中间件服务
func serviceStartall() {
	redis_path := fmt.Sprintf("/etc/redis/redis-6380.conf")
	redis_sentinel_path := fmt.Sprintf("/etc/redis/sentinel.conf")
	filebeat_path := fmt.Sprintf("/etc/filebeat/filebeat.yml")

	for _, middlewareservice := range []string{
		"nginx", "keepalived", "haproxy", "zabbix", "filebeat",
		"elasticsearch", "logstash", "kibana", "redis-server", "redis-sentinel"} {
		_cmd = fmt.Sprintf("whereis %s | awk -F ':' '{print $2}' | grep -v ^$", middlewareservice)
		_cmd = runLinuxCmdWithPureReturn(_cmd)
		// fmt.Println("第一次执行" + _cmd)
		if _cmd != "" {

			if middlewareservice == "redis-server" && Exists(redis_path) {
				middlewareservice = "redis"
				_cmd = serviceStartPure(middlewareservice)
				runLinuxCmdWithPureReturn(_cmd)
				fmt.Println(middlewareservice + " 服务启动 Success")
			} else if middlewareservice == "redis-sentinel" && Exists(redis_sentinel_path) {
				_cmd = serviceStartPure(middlewareservice)
				runLinuxCmdWithPureReturn(_cmd)
				fmt.Println(middlewareservice + " 服务启动 Success")
			} else if middlewareservice == "filebeat" && Exists(filebeat_path) {
				_cmd = serviceStartPure(middlewareservice)
				runLinuxCmdWithPureReturn(_cmd)
				fmt.Println(middlewareservice + " 服务启动 Success")
			}

		}
	}

	//判断tar.gz安装的中间件服务状态
	for _, middlewareservice := range []string{"zookeeper*", "kafka*", "redis_exporter", "kafka_exporter"} {
		_cmd = fmt.Sprintf("ls -d  /opt/app/%s 2>/dev/null", middlewareservice)
		_cmd = runLinuxCmdWithPureReturn(_cmd)
		// fmt.Println("第一次执行" + _cmd)
		if _cmd != "" {
			if middlewareservice == "redis_exporter" {
				redisExporterStart()
			} else if middlewareservice == "kafka_exporter" {
				kafkaExporterStart()
			} else if middlewareservice == "zookeeper*" {
				middlewareservice = "zookeeper"
				_cmd = serviceStartPure(middlewareservice)
				runLinuxCmdWithPureReturn(_cmd)
				fmt.Println(middlewareservice + " 服务启动 Success")
			} else if middlewareservice == "kafka*" {
				middlewareservice = "kafka"
				_cmd = serviceStartPure(middlewareservice)
				runLinuxCmdWithPureReturn(_cmd)
				fmt.Println(middlewareservice + " 服务启动 Success")
			}

		}
	}

}

func serviceStopall() {
	redis_path := fmt.Sprintf("/etc/redis/redis-6380.conf")
	redis_sentinel_path := fmt.Sprintf("/etc/redis/sentinel.conf")
	filebeat_path := fmt.Sprintf("/etc/filebeat/filebeat.yml")

	for _, middlewareservice := range []string{
		"nginx", "keepalived", "haproxy", "zabbix", "filebeat",
		"elasticsearch", "logstash", "kibana", "redis-server", "redis-sentinel"} {
		_cmd = fmt.Sprintf("whereis %s | awk -F ':' '{print $2}' | grep -v ^$", middlewareservice)
		_cmd = runLinuxCmdWithPureReturn(_cmd)
		// fmt.Println("第一次执行" + _cmd)
		if _cmd != "" {

			if middlewareservice == "redis-server" && Exists(redis_path) {
				middlewareservice = "redis"
				_cmd = serviceStopPure(middlewareservice)
				runLinuxCmd(_cmd)
			} else if middlewareservice == "redis-sentinel" && Exists(redis_sentinel_path) {
				_cmd = serviceStopPure(middlewareservice)
				runLinuxCmd(_cmd)
			} else if middlewareservice == "filebeat" && Exists(filebeat_path) {
				_cmd = serviceStopPure(middlewareservice)
				runLinuxCmd(_cmd)
			}

		}
	}

	//判断tar.gz安装的中间件服务状态
	for _, middlewareservice := range []string{"zookeeper*", "kafka*", "redis_exporter", "kafka_exporter"} {
		_cmd = fmt.Sprintf("ls -d  /opt/app/%s 2>/dev/null", middlewareservice)
		_cmd = runLinuxCmdWithPureReturn(_cmd)
		// fmt.Println("第一次执行" + _cmd)
		if _cmd != "" {
			if middlewareservice == "redis_exporter" || middlewareservice == "kafka_exporter" {
				_cmd = serviceStopPure(middlewareservice)
				runLinuxCmd(_cmd)
			} else if middlewareservice == "zookeeper*" {
				middlewareservice = "zookeeper"
				_cmd = serviceStopPure(middlewareservice)
				runLinuxCmd(_cmd)
			} else if middlewareservice == "kafka*" {
				middlewareservice = "kafka"
				_cmd = serviceStopPure(middlewareservice)
				runLinuxCmd(_cmd)
			}

		}
	}

}

//启动的命令
func serviceStart(service string) {
	fmt.Println("--------------------正在启动" + service + "服务-------------------")

	if service == "kafka_exporter" {
		kafkaExporterStart()
	} else if service == "redis_exporter" {
		redisExporterStart()
	} else if service == "filebeat" {
		_cmd = fmt.Sprintf("service %s start", service)
		runLinuxCmd(_cmd)
	} else {
		_cmd = serviceStartPure(service)
		runLinuxCmd(_cmd)
		time.Sleep(3 * time.Second)
		serviceStatus(service)
		time.Sleep(3 * time.Second)
		fmt.Println("--------------------现在查看服务" + service + "日志-------------------")
		tailfServiceLog(service)
	}

}

func serviceStartPure(service string) string {
	if service == "redis" {
		_cmd = fmt.Sprintf("redis-server /etc/redis/redis-6380.conf")
	} else if service == "redis-sentinel" {
		_cmd = fmt.Sprintf("redis-sentinel /etc/redis/sentinel.conf")
	} else if service == "haproxy" {
		_cmd = fmt.Sprintf("/usr/local/haproxy/sbin/haproxy -f /usr/local/haproxy/etc/haproxy.cfg")
	} else if service == "kafka" {
		_cmd = fmt.Sprintf("source /etc/profile && cd %s && ./bin/kafka-server-start.sh -daemon config/server.properties", findRealDir(service))
	} else if service == "zookeeper" {
		_cmd = fmt.Sprintf("source /etc/profile && cd %s && ./bin/zkServer.sh start", findRealDir(service))
	}
	// } else if service == "filebeat" {
	// 	_cmd = fmt.Sprintf("service %s start", service)
	// } else if service == "kafka_exporter" {
	// 	// _cmd = fmt.Sprintf("cd /opt/app/kafka_exporter && nohup ./kafka_exporter --kafka.server=%s:9092 > nohup.out 2>&1 &", getPrivateIpAddress())
	// 	kafkaExporterStart()
	// } else if service == "redis_exporter" {
	// 	// _cmd = fmt.Sprintf("cd /opt/app/redis_exporter && nohup ./redis_exporter  -redis.addr %s -redis.password 'F6x7uVBNovIl1Z@J' -web.listen-address ':9121' > nohup.out 2>&1 &", getPrivateIpAddress())
	// 	redisExporterStart()
	// }
	return _cmd
}

func serviceStop(service string) {
	fmt.Println("--------------------正在停止" + service + "服务-------------------")
	_cmd = serviceStopPure(service)
	runLinuxCmd(_cmd)
	time.Sleep(3 * time.Second)
	serviceStatus(service)
}

func serviceStopPure(service string) string {
	if service == "redis" {
		_cmd = fmt.Sprintf("source /etc/profile && ps -ef | grep -w redis-server | grep -v grep |  awk '{print $2}' | xargs kill")
	} else if service == "redis-sentinel" {
		_cmd = fmt.Sprintf("source /etc/profile && ps -ef | grep -w redis-sentinel | grep -v grep |  awk '{print $2}' | xargs kill")
	} else if service == "haproxy" || service == "redis-sentinel" || service == "kafka_exporter" || service == "redis_exporter" {
		_cmd = fmt.Sprintf("source /etc/profile && ps -ef | grep -w %s | grep -v grep |  awk '{print $2}' | xargs kill", service)
	} else if service == "kafka" {
		_cmd = fmt.Sprintf("source /etc/profile && cd %s && ./bin/kafka-server-stop.sh config/server.properties", findRealDir(service))
	} else if service == "zookeeper" {
		_cmd = fmt.Sprintf("source /etc/profile && cd %s && ./bin/zkServer.sh stop", findRealDir(service))
	} else if service == "filebeat" {
		_cmd = fmt.Sprintf("service %s stop", service)
	}
	return _cmd
}

func kafkaHandle(action string, service string, keyword string) {
	if service == "kafka" {
		if action == "topiclist" || action == "tlist" {
			//查看topic列表
			_cmd = fmt.Sprintf("cd %s && ./bin/kafka-topics.sh   --bootstrap-server %s:9092  --list", findRealDir(service), getPrivateIpAddress())
		} else if action == "topiccreate" || action == "tcreate" {
			//创建topic 指定3副本 15分区
			_cmd = fmt.Sprintf("cd %s && ./bin/kafka-topics.sh --create --bootstrap-server %s:9092 --topic %s --replication-factor 3 --partitions 15", findRealDir(service), getPrivateIpAddress(), keyword)
		} else if action == "topicdelete" || action == "tdelete" {
			//删除topic
			_cmd = fmt.Sprintf("cd %s && ./bin/kafka-topics.sh --delete --bootstrap-server %s:9092 --topic %s", findRealDir(service), getPrivateIpAddress(), keyword)
		} else if action == "topicdescribe" || action == "tdescribe" {
			//查看topic同步状态
			_cmd = fmt.Sprintf("cd %s && ./bin/kafka-topics.sh --bootstrap-server %s:9092   --topic %s   --describe", findRealDir(service), getPrivateIpAddress(), keyword)
		} else if action == "consumergrouplist" || action == "clist" {
			//查看消费组列表
			_cmd = fmt.Sprintf("cd %s && ./bin/kafka-consumer-groups.sh --list --bootstrap-server %s:9092", findRealDir(service), getPrivateIpAddress())
		} else if action == "consumergroupdescribe" || action == "cdescribe" {
			//查看消费组偏移情况
			_cmd = fmt.Sprintf("cd %s && ./bin/kafka-consumer-groups.sh --bootstrap-server %s:9092 --describe --group  %s", findRealDir(service), getPrivateIpAddress(), keyword)
		} else if action == "du" {
			//计算kafka topic大小
			_cmd = fmt.Sprintf("cd /opt/data/kafka  && du -ch  %s-* | tail -n 1 | awk '{print $1}'", keyword)
		} else if action == "get" {
			//获取kafka消息消费情况
			_cmd = fmt.Sprintf("%sbin/kafka-console-consumer.sh  --bootstrap-server %s:9092   --topic %s --from-beginning --timeout-ms 10000", findRealDir(service), getPrivateIpAddress(), keyword)
		}
		runLinuxCmd(_cmd)
	}
}

func logHandle(action string, service string, keyword string) {
	logfile = findRealLogfile(service)
	if action == "log" {
		//查看最近300条日志
		_cmd = fmt.Sprintf("tail -n 100 %s", logfile)
	} else if action == "logr" {
		_cmd = fmt.Sprintf("grep %s %s", keyword, logfile)
	} else if action == "logs" {
		_cmd = fmt.Sprintf("tail -n 100 %s | grep -C 5 success", logfile)
	}

	runLinuxCmd(_cmd)
	if action == "logf" {
		logfile = findRealLogfile(service)
		tailLog(logfile)
	}
}

///////////////////////////////////////获取信息的命令begin///////////////////////////////////////

//获取中间件的家目录
func findRealDir(service string) string {
	if service == "kafka" {
		realdir = runLinuxCmdWithPureReturn("find /opt/app -name kafka-topics.sh | awk -F 'bin' '{print $1}' | tail -n 1")
	} else if service == "zookeeper" {
		realdir = runLinuxCmdWithPureReturn("find /opt/app -name zkCli.sh | awk -F 'bin' '{print $1}' | tail -n 1")
	}
	return realdir
}

//获取真实的日志路径
func findRealLogfile(service string) string {
	if service == "redis" {
		logfile = fmt.Sprintf("/yjb3_logs/redis/redis-6380.out")
	} else if service == "haproxy" {
		logfile = fmt.Sprintf("/usr/local/haproxy/logs/haproxy.log")
	} else if service == "kafka" {
		logfile = runLinuxCmdWithPureReturn("if [[ $(find /opt/app/kafka*/logs/ -name server.log | wc -l) -eq 1 ]]; then echo $(find /opt/app/kafka*/logs/ -name server.log); else echo 'notonlyone.log'; fi")
	} else if service == "zookeeper" {
		logfile = runLinuxCmdWithPureReturn("if [[ $(find /opt/app/zookeeper*/logs/ -name zookeeper.out | wc -l) -eq 1 ]]; then echo $(find /opt/app/zookeeper*/logs/ -name zookeeper.out); else echo 'notonlyone.log'; fi")
	}
	return logfile
}

// 获取服务器的内网ip
func getPrivateIpAddress() string {
	addrs, err := net.InterfaceAddrs()
	if err != nil {
		// fmt.Println(err)
		return "127.0.0.1"
	}
	for _, addr := range addrs {
		if ipnet, ok := addr.(*net.IPNet); ok && !ipnet.IP.IsLoopback() {
			if ipnet.IP.To4() != nil {
				privateipaddress := ipnet.IP.String()
				return privateipaddress
			}
		}
	}
	return "127.0.0.1"
}

//根据进程名称获取进程ID
func getPid(service string) string {
	if service == "haproxy" {
		pid = runLinuxCmdWithPureReturn("ps -ef | grep '/usr/local/haproxy/sbin/haproxy' | grep -Ev 'grep|mid'  | awk '{print $2}' | tail -n 1")
	}
	return pid
}

///////////////////////////////////////获取信息的命令end///////////////////////////////////////

func tailfServiceLog(service string) {
	logfile = findRealLogfile(service)
	tailLog(logfile)
}

type Result struct {
	Media_id string `json:"media_id"`
}

// 发送本地文件到企业微信
func sendQiyeWechat(filename string) {
	key := ""
	//上传文件到企业微信临时的云并获取media_id, media_id有效期三天
	_cmd := fmt.Sprintf(`curl -X POST "https://qyapi.weixin.qq.com/cgi-bin/webhook/upload_media?key=%s&type=file" -F "file=@%s"`, key, filename)
	str := runLinuxCmdWithPureReturn(_cmd)
	var result Result
	err := json.Unmarshal([]byte(str), &result)
	if err != nil {
		fmt.Println("erorr", err)
		return
	}
	//获得media_id
	// fmt.Println(result.Media_id)
	media_id := result.Media_id
	// 发送临时文件到企业微信
	_cmd = fmt.Sprintf(`curl -s -H 'Content-Type:application/json' -d '{"msgtype":"file","file":{"media_id":"'%s'"}}' "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=%s"`, media_id, key) // 修改了此行
	runLinuxCmd(_cmd)
}

//输出帮助
func Help() {
	fmt.Println(help_content)
}

// 查看当前的程序版本
func Version() {
	var buf syscall.Utsname
	err := syscall.Uname(&buf)
	if err != nil {
		fmt.Println("Error:", err)
		return
	}
	release := make([]byte, len(buf.Release))
	var i int
	for ; i < len(buf.Release); i++ {
		if buf.Release[i] == 0 {
			break
		}
		release[i] = byte(buf.Release[i])
	}
	_cmd = fmt.Sprintf("current version is %s \nKernel Version is %s", version, string(release[:i]))
	fmt.Println(_cmd)
}

//运行linux 命令
func runLinuxCmd(cmd string) string {
	// fmt.Println("##############################################################################################")
	fmt.Println("############ Running Linux cmd :" + cmd + " ############")
	result := exec.Command("/bin/sh", "-c", cmd)
	output, err := result.Output()
	if err != nil {
		fmt.Printf("没有返回结果\n")
	}

	fmt.Printf(string(output))
	return string(output)
}

//执行命令并获取纯净的返回值（不含其他字符）
func runLinuxCmdWithPureReturn(cmd string) string {
	result := exec.Command("/bin/sh", "-c", cmd)
	output, err := result.Output()
	if err != nil {
		fmt.Printf("")
	}
	//去除空格
	str := strings.Replace(string(output), " ", "", -1)
	//去除换行符
	str = strings.Replace(str, "\n", "", -1)

	return str
}

//tail log的标准模块
func tailLog(fileName string) string {
	config := tail.Config{
		ReOpen:    true,                                 // 重新打开
		Follow:    true,                                 // 是否跟随
		Location:  &tail.SeekInfo{Offset: 0, Whence: 2}, // 从文件的哪个地方开始读
		MustExist: false,                                // 文件不存在不报错
		Poll:      true,
	}
	tails, err := tail.TailFile(fileName, config)
	if err != nil {
		fmt.Println("tail file failed, err:", err)
	}
	var (
		line *tail.Line
		ok   bool
	)
	for {
		line, ok = <-tails.Lines
		if !ok {
			fmt.Printf("tail file close reopen, filename:%s\n", tails.Filename)
			time.Sleep(time.Second)
			continue
		}
		fmt.Println(line.Text)
	}
}

func main() {

	if len(os.Args) == 1 {
		// 只有1个参数，比如输入mid,直接弹出help文档
		action = "help"
	} else if len(os.Args) == 2 {
		// 只有2个参数，则执行的动作就是参数名
		action = os.Args[1]
	} else if len(os.Args) == 3 {
		action = os.Args[1]
		argname = os.Args[2]
	} else {
		action = os.Args[1]
		argname = os.Args[2]
		keyword = os.Args[3]
	}

	if argname == "ha" {
		argname = "haproxy"
	} else if argname == "rds" {
		argname = "redis"
	} else if argname == "ka" {
		argname = "kafka"
	} else if argname == "zk" {
		argname = "zookeeper"
	}

	if action == "start" {
		serviceStart(argname)
	} else if action == "status" || action == "st" {
		serviceStatus(argname)
	} else if action == "startall" {
		serviceStartall()
	} else if action == "stopall" {
		serviceStopall()
	} else if action == "reload" {
		serviceReload(argname)
	} else if action == "master" || action == "ma" {
		serviceMaster(argname)
	} else if action == "monitor" {
		serviceMonitor(argname)
	} else if action == "replicate" || action == "rep" {
		serviceReplicate(argname, keyword)
	} else if action == "leader" {
		serviceLeader(argname)
	} else if action == "scan" {
		scanEndpoint(argname)
	} else if action == "stop" {
		serviceStop(argname)
	} else if action == "check" {
		checkMiddlewareService()
	} else if action == "log" || action == "logr" || action == "logf" || action == "logs" {
		logHandle(action, argname, keyword)
	} else if action == "tlist" || action == "topiclist" || action == "tcreate" || action == "topiccreate" || action == "tdelete" || action == "topicdelete" {
		kafkaHandle(action, argname, keyword)
	} else if action == "consumergrouplist" || action == "clist" || action == "topicdescribe" || action == "tdescribe" || action == "consumergroupdescribe" || action == "cdescribe" {
		kafkaHandle(action, argname, keyword)
	} else if action == "du" || action == "get" {
		kafkaHandle(action, argname, keyword)
	} else if action == "send" {
		sendQiyeWechat(argname)
	} else if action == "help" {
		Help()
	} else if action == "version" {
		Version()
	} else {
		Help()
	}
}
