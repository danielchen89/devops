// 基础服务器运维操作工具
package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"net"
	"os"
	"os/exec"
	"sort"
	"strconv"
	"strings"
	"syscall"
	"time"

	"github.com/hpcloud/tail"
)

var err string
var action, argname, service, keyword, servicetype string
var _cmd, _cmd1, _cmd2, pid, lognums string
var logname, logfile string
var dirs []string

//获取当前时间戳作为版本号，精确到分
var version string = "20231230.1330"
var help_content string = `
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
	查看服务的最新5条|10条错误日志 : svc logen5|logen10 服务名 老师
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

func findWrapperLog(service string) string {
	_cmd = fmt.Sprintf("cd  /opt/app/%s/logs/ && ls -l -rt | grep log  | grep 'wrapper' | tail -n 1 | awk '{print $9}'", service)
	logname = runLinuxCmdWithPureReturn(_cmd)
	return logname
}

//查找真实的日志文件
//日志名和服务名一致，选取 服务名.log 作为日志文件
//日志名和服务名不一致，选取最新时间戳的文件作为日志文件
func findRealLogfile(service string) string {
	service, servicetype = isJarOrWar(service)
	if servicetype == "jar" {
		_cmd = fmt.Sprintf("cd  /opt/app/%s/logs/ && ls -l -rt | grep log  | grep -v -E -w 'wrapper|gc|zip|metrics' | tail -n 1 | awk '{print $9}'", service)
	} else if servicetype == "war" {
		fmt.Println("tomcat service is :" + service)
		_cmd = fmt.Sprintf("cd /opt/app/%s/logs/ && ls -l -rt | grep -v -E -w 'wrapper|gc|zip|metrics|localhost|manager' |tail -n 1 | awk '{print $9}'", service)

	}
	logname = runLinuxCmdWithPureReturn(_cmd)
	if logname == "" {
		logname = findWrapperLog(service)
	}
	return logname
}

//判断服务是jar包还是war包
func isJarOrWar(service string) (string, string) {
	consul_path := fmt.Sprintf("/opt/app/%s.d/run.sh", service)
	jar_path := fmt.Sprintf("/opt/app/%s/bin/run.sh", service)
	war_path := fmt.Sprintf("/opt/app/%s/bin/startup.sh", service)

	if Exists(jar_path) {
		servicetype = "jar"
	} else if Exists(war_path) {
		servicetype = "war"
	} else if Exists(consul_path) {
		servicetype = "consul"
	} else {
		servicetype = "else"
	}

	return service, servicetype
}

//判断是存在jar包还是war包
func existJarOrWar(dir string) string {
	consul_path := fmt.Sprintf(dir + "/run.sh")
	jar_path := fmt.Sprintf(dir + "/bin/run.sh")
	war_path := fmt.Sprintf(dir + "/bin/startup.sh")

	if Exists(jar_path) {
		servicetype = "jar"
	} else if Exists(war_path) {
		servicetype = "war"
	} else if Exists(consul_path) {
		servicetype = "consul"
	} else {
		servicetype = "else"
	}

	return servicetype
}

//判断端口
// 比如 svc : 2000
// 执行查找
// netstat -lntup | grep 2000
// ps -ef | grep 2000
func colon(port string) {
	_cmd = fmt.Sprintf("netstat -lntup | grep -w %s", port)
	runLinuxCmd(_cmd)
	_cmd = fmt.Sprintf("ps -ef | grep $(netstat -lntup | grep -w %s | head -n 1 | awk '{print $7}' | awk -F '/' '{print $1}') | grep -v -E 'grep|svc'", port)
	runLinuxCmd(_cmd)
	_cmd = fmt.Sprintf("ss -lntup | grep -w %s", port)
	runLinuxCmd(_cmd)
	_cmd = fmt.Sprintf("lsof -i:%s", port)
	runLinuxCmd(_cmd)
}

//consul服务启动

func consulStart() {
	cmd := exec.Command("sh", "-c", "source /etc/profile && cd /opt/app/consul.d && nohup consul agent --config-dir=config-dir &")

	// 设置命令执行的工作目录
	cmd.Dir = "/opt/app/consul.d"

	// 将命令的输出重定向到标准输出
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	// 执行命令
	err := cmd.Run()
	if err != nil {
		log.Fatal(err)
	}
	fmt.Println("###############consul服务启动##################")
}

//启动的命令
func serviceStart(service string) {
	service, servicetype = isJarOrWar(service)
	serviceStatus(service)
	time.Sleep(3 * time.Second)
	fmt.Println("--------------------正在启动" + service + "服务-------------------")
	if servicetype == "jar" {
		_cmd = fmt.Sprintf("source /etc/profile && cd /opt/app/%s/bin/ && sh ./run.sh start", service)
	} else if servicetype == "war" {
		_cmd = fmt.Sprintf("source /etc/profile && cd /opt/app/%s/bin/ && sh ./startup.sh", service)
	}
	runLinuxCmd(_cmd)
	time.Sleep(3 * time.Second)

	if servicetype == "consul" {
		consulStart()
		time.Sleep(5 * time.Second)
	}

	fmt.Println("--------------------现在查看服务" + service + "日志-------------------")
	tailfServiceLog(service)

}

//停止的命令
func serviceStop(service string) {
	service, servicetype = isJarOrWar(service)
	fmt.Println("--------------------正在停止" + service + "服务-------------------")
	if servicetype == "jar" {
		_cmd = fmt.Sprintf("source /etc/profile && cd /opt/app/%s/bin/ && sh ./run.sh stop", service)
	} else if servicetype == "war" {
		_cmd = fmt.Sprintf("source /etc/profile && ps -ef | grep -w %s/conf | grep -v grep |  awk '{print $2}' | xargs kill -9", service)
	} else if servicetype == "consul" {
		_cmd = fmt.Sprintf("source /etc/profile && ps -ef | grep %s | grep config-dir |  awk '{print $2}' | xargs kill -9", service)
	}
	runLinuxCmd(_cmd)
	time.Sleep(3 * time.Second)
	serviceStatus(service)

}

//重启的命令
func serviceRestart(service string) {
	service, servicetype = isJarOrWar(service)
	fmt.Println("--------------------现在查看服务" + service + "状态-------------------")
	serviceStatus(service)
	time.Sleep(3 * time.Second)
	fmt.Println("--------------------正在重启" + service + "服务-------------------")
	if servicetype == "jar" {
		_cmd = fmt.Sprintf("source /etc/profile && cd /opt/app/%s/bin/ && sh ./run.sh stop && sh ./run.sh start", service)
		runLinuxCmd(_cmd)
	} else if servicetype == "war" {
		//关闭tomcat进程并删除 Catalina下面的文件
		// _cmd1 = fmt.Sprintf("source /etc/profile && cd /opt/app/%s/ && sh ./bin/shutdown.sh -force && rm -rf ./work/Catalina/*", service)
		_cmd1 = fmt.Sprintf("source /etc/profile && ps -ef | grep -w %s/conf | grep -v grep |  awk '{print $2}' | xargs kill -9", service)
		runLinuxCmd(_cmd1)
		_cmd2 = fmt.Sprintf("source /etc/profile && cd /opt/app/%s/ && sh ./bin/startup.sh", service)
		runLinuxCmd(_cmd2)
	} else if servicetype == "consul" {
		_cmd1 = fmt.Sprintf("source /etc/profile && ps -ef | grep %s | grep config-dir |  awk '{print $2}' | xargs kill -9", service)
		runLinuxCmd(_cmd1)
		consulStart()
	}

	time.Sleep(3 * time.Second)
	fmt.Println("--------------------现在查看服务" + service + "日志-------------------")
	tailfServiceLog(service)
}

func PathExists(path string) bool {
	_, err := os.Stat(path)
	if err == nil {
		return true
	}
	if os.IsNotExist(err) {
		return false
	}
	return false
}

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

func in(target string, str_array []string) bool {
	sort.Strings(str_array)
	index := sort.SearchStrings(str_array, target)
	if index < len(str_array) && str_array[index] == target {
		return true
	}
	return false
}

//先校对时间,启动filebeat,然后启动cousul，最后启动服务

func serviceStartall() {
	// _cmd = fmt.Sprintf("/usr/sbin/ntpdate 192.168.70.92")
	// runLinuxCmd(_cmd)
	checkFzOrProdTime()
	_cmd = fmt.Sprintf("service filebeat start")
	runLinuxCmd(_cmd)
	//启动consul和服务
	getDirList("/opt/app/")
	exclude_list := []string{""}
	for _, dir := range dirs {
		servicetype = existJarOrWar(dir)

		if servicetype == "consul" {
			consulStart()
			time.Sleep(5 * time.Second)
		} else if servicetype == "jar" || servicetype == "war" {
			// 注意tomcat服务这里是完整取出了服务名
			service = dir[9:]
			if in(service, exclude_list) {
				fmt.Println("###########" + service + " 服务不用启动 ###########")
			} else {
				if servicetype == "jar" {
					_cmd = fmt.Sprintf("source /etc/profile && cd /opt/app/%s/bin/ && sh ./run.sh start", service)
					runLinuxCmd(_cmd)
				} else if servicetype == "war" {
					_cmd = fmt.Sprintf("source /etc/profile && cd /opt/app/%s/bin/ && sh ./startup.sh", service)
					runLinuxCmd(_cmd)
				}
			}
		}
	}
}

func serviceStopall() {
	getDirList("/opt/app/")
	exclude_list := []string{""}
	for _, dir := range dirs {
		servicetype = existJarOrWar(dir)
		if servicetype == "consul" {
			_cmd = fmt.Sprintf("source /etc/profile && ps -ef | grep consul | grep config-dir |  awk '{print $2}' | xargs kill -9")
			runLinuxCmd(_cmd)
		}

		if servicetype == "jar" || servicetype == "war" {
			// 注意tomcat服务这里是完整取出了服务名
			service = dir[9:]
			if in(service, exclude_list) {
				fmt.Println("###########" + service + " 服务不用重启 ###########")
			} else {
				if servicetype == "jar" {
					_cmd = fmt.Sprintf("source /etc/profile && cd /opt/app/%s/bin/ && sh ./run.sh stop", service)
					runLinuxCmd(_cmd)
				} else if servicetype == "war" {
					_cmd = fmt.Sprintf("source /etc/profile && cd /opt/app/%s/bin/ && sh ./shutdown.sh", service)
					runLinuxCmd(_cmd)
				}
			}
		}
	}
}

func serviceRestartall() {
	getDirList("/opt/app/")
	exclude_list := []string{"yuser-job"}
	for _, dir := range dirs {
		servicetype = existJarOrWar(dir)
		if servicetype == "consul" {
			_cmd1 = fmt.Sprintf("source /etc/profile && ps -ef | grep consul | grep config-dir |  awk '{print $2}' | xargs kill -9")
			runLinuxCmd(_cmd1)
			consulStart()
		}

		if servicetype == "jar" || servicetype == "war" {
			// 注意tomcat服务这里是完整取出了服务名
			service = dir[9:]
			if in(service, exclude_list) {
				fmt.Println("###########" + service + " 服务不用重启 ###########")
			} else {
				if servicetype == "jar" {
					_cmd = fmt.Sprintf("source /etc/profile && cd /opt/app/%s/bin/ && sh ./run.sh stop && sh ./run.sh start", service)
					runLinuxCmd(_cmd)
				} else if servicetype == "war" {
					_cmd1 = fmt.Sprintf("source /etc/profile && ps -ef | grep -w %s/conf | grep -v grep |  awk '{print $2}' | xargs kill -9", service)
					runLinuxCmd(_cmd1)
					_cmd2 = fmt.Sprintf("source /etc/profile && cd /opt/app/%s/ && sh ./bin/startup.sh", service)
					runLinuxCmd(_cmd2)
				}
			}
		}
	}
}

//检查/opt/app下面所有服务的状态，nginx.kafka,redis等的服务状态
func checkService() {
	//获取/opt/app下所有的服务
	getDirList("/opt/app/")
	for _, dir := range dirs {
		servicetype = existJarOrWar(dir)
		if servicetype == "jar" || servicetype == "war" {
			service = dir[9:]
			_cmd = fmt.Sprintf("ps -ef | grep -w %s/bin | grep -v grep | grep -v svc | wc -l", service)
			threadnums, err := strconv.Atoi(runLinuxCmdWithPureReturn(_cmd))
			if err != nil {
				fmt.Println(err)
			} else {
				if threadnums == 0 {
					fmt.Println(service + "服务启动 Fail!!!")
				} else {
					fmt.Println(service + "服务启动 Success")
				}
			}

		} else if servicetype == "consul" {
			service = "consul"
			_cmd = fmt.Sprintf("source /etc/profile && ps -ef | grep consul | grep config-dir  | grep -v grep | grep -v svc | wc -l")
			threadnums, err := strconv.Atoi(runLinuxCmdWithPureReturn(_cmd))
			if err != nil {
				fmt.Println(err)
			} else {
				if threadnums == 0 {
					fmt.Println(service + "服务启动 Fail!!!")
				} else {
					fmt.Println(service + "服务启动 Success")
				}
			}
		}
	}

	fmt.Println("#########判断中间件的状态##########")
	//判断rpm安装的中间件服务的状态
	for _, middlewareservice := range []string{
		"nginx", "keepalived", "haproxy", "zabbix", "filebeat",
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

	fmt.Println("#########判断时间是否正确##########")
	fmt.Println("对时前的时间： " + time.Now().Format("2006-01-02 15:04:05"))
	_cmd = fmt.Sprintf("/usr/sbin/ntpdate 192.168.70.92")
	checkFzOrProdTime()
	fmt.Println("对时后的时间： " + time.Now().Format("2006-01-02 15:04:05"))
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

//仿真和生产时间校对
//下列检查crontab每日时间同步是否正确
/////////////////////////////////////////////////////////////////////////////////////

func checkFzOrProdTime() {
	ip := getPrivateIP()
	ipPrefix := strings.Join(strings.Split(ip, ".")[:3], ".")

	switch ipPrefix {
	case "192.168.79", "192.168.179", "192.168.180", "192.168.181", "192.168.182":
		_cmd = fmt.Sprintf("/usr/sbin/ntpdate 192.168.79.177")
		runLinuxCmdWithPureReturn(_cmd)
	case "192.168.70", "192.168.170", "192.168.171", "192.168.172", "192.168.173", "192.168.73":
		_cmd = fmt.Sprintf("/usr/sbin/ntpdate 192.168.70.92")
		runLinuxCmdWithPureReturn(_cmd)
	case "192.168.61", "192.168.62", "172.28.60", "172.28.61", "172.28.62", "172.28.63", "172.28.64":
		_cmd = fmt.Sprintf("/usr/sbin/ntpdate 172.28.25.33")
		runLinuxCmdWithPureReturn(_cmd)
	default:
		fmt.Println(ip + ": 未匹配")
	}

}

func getPrivateIP() string {
	interfaces, err := net.Interfaces()
	if err != nil {
		fmt.Println("无法获取网络接口列表：", err)
		return ""
	}

	var ipList []string
	for _, iface := range interfaces {
		addrs, err := iface.Addrs()
		if err != nil {
			fmt.Printf("无法获取接口 %s 的地址列表：%s\n", iface.Name, err)
			continue
		}

		for _, addr := range addrs {
			ipNet, ok := addr.(*net.IPNet)
			if ok && !ipNet.IP.IsLoopback() && ipNet.IP.To4() != nil {
				ip := ipNet.IP.String()
				if !strings.HasPrefix(ip, "127.") {
					ipList = append(ipList, ip)
				}
			}
		}
	}

	if len(ipList) == 0 {
		fmt.Println("找不到可用的IP地址")
		return ""
	}

	// fmt.Println("本机的IP地址列表：")
	for _, ip := range ipList {
		// fmt.Println(ip)
		return ip
	}
	return ""
}

func checkTimeCron() {
	// interfaces, err := net.Interfaces()
	// if err != nil {
	// 	fmt.Println("无法获取网络接口列表：", err)
	// 	return
	// }

	// var ipList []string
	// for _, iface := range interfaces {
	// 	addrs, err := iface.Addrs()
	// 	if err != nil {
	// 		fmt.Printf("无法获取接口 %s 的地址列表：%s\n", iface.Name, err)
	// 		continue
	// 	}

	// 	for _, addr := range addrs {
	// 		ipNet, ok := addr.(*net.IPNet)
	// 		if ok && !ipNet.IP.IsLoopback() && ipNet.IP.To4() != nil {
	// 			ip := ipNet.IP.String()
	// 			if !strings.HasPrefix(ip, "127.") {
	// 				ipList = append(ipList, ip)
	// 			}
	// 		}
	// 	}
	// }

	// for _, ip := range ipList {
	ip := getPrivateIP()
	ipPrefix := strings.Join(strings.Split(ip, ".")[:3], ".")

	switch ipPrefix {
	case "172.16.8", "172.16.34":
		fmt.Println(ip + ": 金桥或荷丹idc")
		crontabNum := countCrontabOccurrences("/var/spool/cron/root", "172.16.1.18")
		if crontabNum == 0 {
			fmt.Println("时钟服务器地址不是本机房的,更新时钟服务器地址")
			removeCrontabLine("/var/spool/cron/root", "ntpdate")
			appendCrontabLine("/var/spool/cron/root", "02 06 * * * /usr/sbin/ntpdate 172.16.1.18 >> /tmp/ntpdate.log 2>&1")
		}
	case "197.1.14":
		fmt.Println(ip + ": 西信idc")
		crontabNum := countCrontabOccurrences("/var/spool/cron/root", "197.1.1.104")
		if crontabNum == 0 {
			fmt.Println("时钟服务器地址不是本机房的,更新时钟服务器地址")
			removeCrontabLine("/var/spool/cron/root", "ntpdate")
			appendCrontabLine("/var/spool/cron/root", "02 06 * * * /usr/sbin/ntpdate 197.1.1.104 >> /tmp/ntpdate.log 2>&1")
		}
	case "192.168.79", "192.168.179", "192.168.180", "192.168.181", "192.168.182":
		fmt.Println(ip + ": 79dc")
		crontabNum := countCrontabOccurrences("/var/spool/cron/root", "192.168.79.177")
		if crontabNum == 0 {
			fmt.Println("时钟服务器地址不是本机房的,更新时钟服务器地址")
			removeCrontabLine("/var/spool/cron/root", "ntpdate")
			appendCrontabLine("/var/spool/cron/root", "02 06 * * * /usr/sbin/ntpdate 192.168.79.177 >> /tmp/ntpdate.log 2>&1")
		}
	case "192.168.70", "192.168.170", "192.168.171", "192.168.172", "192.168.173", "192.168.73":
		fmt.Println(ip + ": 70dc")
		crontabNum := countCrontabOccurrences("/var/spool/cron/root", "192.168.70.92")
		if crontabNum == 0 {
			fmt.Println("时钟服务器地址不是本机房的,更新时钟服务器地址")
			removeCrontabLine("/var/spool/cron/root", "ntpdate")
			appendCrontabLine("/var/spool/cron/root", "02 06 * * * /usr/sbin/ntpdate 192.168.70.92 >> /tmp/ntpdate.log 2>&1")
		}
	case "192.168.61", "192.168.62", "172.28.60", "172.28.61", "172.28.62", "172.28.63", "172.28.64":
		fmt.Println(ip + ": fz")
		crontabNum := countCrontabOccurrences("/var/spool/cron/root", "172.28.25.33")
		if crontabNum == 0 {
			fmt.Println("时钟服务器地址不是本机房的,更新时钟服务器地址")
			removeCrontabLine("/var/spool/cron/root", "ntpdate")
			appendCrontabLine("/var/spool/cron/root", "00 */2 * * * /usr/sbin/ntpdate 172.28.25.33 && hwclock -w >> /tmp/ntpdate.log 2>&1")
		}
	default:
		fmt.Println(ip + ": 未匹配")
	}
	// }
}

// 统计指定文件中包含某字符串的行数
func countCrontabOccurrences(filename, searchString string) int {
	file, err := os.Open(filename)
	if err != nil {
		return 0
	}
	defer file.Close()

	count := 0
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		if strings.Contains(scanner.Text(), searchString) {
			count++
		}
	}

	return count
}

// 从指定文件中移除包含某字符串的行
func removeCrontabLine(filename, searchString string) {
	cmd := exec.Command("sed", "-i", "/"+searchString+"/d", filename)
	err := cmd.Run()
	if err != nil {
		fmt.Println("无法移除Crontab行：", err)
	}
}

// 向指定文件中追加一行内容
func appendCrontabLine(filename, line string) {
	f, err := os.OpenFile(filename, os.O_APPEND|os.O_WRONLY, 0644)
	if err != nil {
		fmt.Println("无法追加Crontab行：", err)
		return
	}
	defer f.Close()

	if _, err = f.WriteString(line + "\n"); err != nil {
		fmt.Println("无法追加Crontab行：", err)
	}
}

//////////////////////////////////////////////////////////////////////////////////////

//列出服务器上所有的服务
func lsService() {
	//获取/opt/app下所有的服务
	getDirList("/opt/app/")
	for _, dir := range dirs {
		servicetype = existJarOrWar(dir)
		if servicetype == "consul" {
			service = "consul"
			fmt.Println(service)
		}
		if servicetype == "jar" || servicetype == "war" {
			service = dir[9:]
			fmt.Println(service)
		}
	}
	fmt.Println("#########获取服务器上的中间件服务信息##########")
	//获取rpm安装的中间件服务
	for _, middlewareservice := range []string{"nginx", "keepalived", "haproxy", "zabbix", "filebeat",
		"elasticsearch", "logstash", "kibana", "redis-server", "redis-sentinel"} {
		_cmd = fmt.Sprintf("whereis %s | awk -F ':' '{print $2}' | grep -v ^$", middlewareservice)
		_cmd = runLinuxCmdWithPureReturn(_cmd)
		// fmt.Println("第一次执行" + _cmd)
		if _cmd != "" {
			fmt.Println(middlewareservice)
		}
	}

	//获取tar.gz安装的中间件服务
	for _, middlewareservice := range []string{"zookeeper", "kafka"} {
		_cmd = fmt.Sprintf("ls -d  /opt/app/%s 2>/dev/null", middlewareservice)
		_cmd = runLinuxCmdWithPureReturn(_cmd)
		// fmt.Println("第一次执行" + _cmd)
		if _cmd != "" {
			fmt.Println(middlewareservice)
		}
	}
}

//根据进程名称获取进程ID
func getPid(service string) string {
	service, servicetype = isJarOrWar(service)
	// _cmd = `source /etc/profile && pgrep -f ` + service + `| tail -n 1`
	//_cmd = `ps ux | awk '/opt/app/` + service + `/bin/ && !/awk/ && /\/opt\/app/ {print $2}' | tail -n 1`
	// _cmd := `ps ux | awk '/` + service + `/ && !/awk/ && /\/opt\/app\/` + service + `\/bin/ {print $2}' | tail -n 1`
	_cmd := `ps -ef | grep '/opt/app/` + service + `/' | grep -v grep | awk '{print $2}' | tail -n 1`
	// fmt.Println("############ Get pid cmd :" + _cmd + " ############")
	pid = runLinuxCmdWithPureReturn(_cmd)
	fmt.Println("pid: " + pid)
	return pid
}

//根据进程名称获取进程ID
func getPid2(service string) string {
	service, servicetype = isJarOrWar(service)
	// _cmd = `source /etc/profile && pgrep -f ` + service + `| tail -n 1`
	// _cmd = `ps ux | awk '/opt/app/` + service + `/bin/ && !/awk/ && /\/opt\/app/ {print $2}' | tail -n 1`
	// _cmd := `ps ux | awk '/` + service + `/ && !/awk/ && /\/opt\/app\/` + service + `\/bin/ {print $2}' | head -n 1`
	_cmd := `ps -ef | grep '/opt/app/` + service + `/' | grep -v grep | awk '{print $2}' | head -n 1`
	// fmt.Println("############ Get pid cmd :" + _cmd + " ############")
	pid = runLinuxCmdWithPureReturn(_cmd)
	fmt.Println("pid: " + pid)
	return pid
}

//实现效果cat filebeat.yml | grep -v ^# | grep -v ^$ | grep -v "  #"
func fileCat(filename string) {
	_cmd = fmt.Sprintf("cat %s | grep -v ^# | grep -v ^$ | grep -v '  #'", filename)
	runLinuxCmd(_cmd)
}

type Result struct {
	Media_id string `json:"media_id"`
}

// 发送本地文件到企业微信
func sendQiyeWechat(filename string) {

	_cmd = fmt.Sprintf("cat /etc/resolv.conf | grep -v ^# | grep -E '172.16.9.200|172.16.10.200|172.16.25.200|197.1.254.200|197.1.11.200' wc -l")
	_cmd = runLinuxCmdWithPureReturn(_cmd)
	// fmt.Println("第一次执行" + _cmd)
	if _cmd == "1" {
		fmt.Println("外网dns配置正确")
	} else {
		fmt.Println("外网dns配置不正确，qyapi.weixin.qq.com可能无法解析！")
	}

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

//列出/opt/app下某个服务的所有目录.并快捷进入
func confService(service string) {
	_cmd = fmt.Sprintf("find /opt/app/%s/ -name *.properties", service)
	runLinuxCmd(_cmd)
	_cmd = fmt.Sprintf("ls /opt/app/%s/conf | grep -v -E \"wrapper.conf|logback.xml\"", service)
	runLinuxCmd(_cmd)
	_cmd = fmt.Sprintf("cat /opt/app/%s/conf/*.properties | grep -v ^# | grep -v ^$ | grep -v '  #'", service)
	runLinuxCmd(_cmd)
}

//动态查看服务日志
func tailfServiceLog(service string) {
	service, servicetype = isJarOrWar(service)
	logname = findRealLogfile(service)

	if servicetype == "jar" || servicetype == "war" {
		logfile = fmt.Sprintf("/opt/app/%s/logs/%s", service, logname)
	} else if servicetype == "consul" {
		logfile = fmt.Sprintf("/opt/app/%s.d/nohup.out", service)
	}
	tailLog(logfile)
}

//查看今天日志的并进行过滤
func logFilter(action string, service string, keyword string) {
	service, servicetype = isJarOrWar(service)
	logname = findRealLogfile(service)
	if action == "logr" {
		_cmd = fmt.Sprintf("grep %s /opt/app/%s/logs/%s", keyword, service, logname)
	} else if action == "logo" {
		_cmd = fmt.Sprintf("cat /opt/app/%s/logs/%s | %s", service, logname, keyword)
	}
	runLinuxCmd(_cmd)
}

func logHandle(action string, service string) {
	service, servicetype = isJarOrWar(service)
	logname = findRealLogfile(service)
	if action == "log" {
		//查看最近300条日志
		if servicetype == "jar" || servicetype == "war" {
			_cmd = fmt.Sprintf("tail -n 300 /opt/app/%s/logs/%s", service, logname)
		} else if servicetype == "consul" {
			_cmd = fmt.Sprintf("tail -n 300 /opt/app/consul.d/nohup.out")
		}
	} else if action == "loge" {
		//查看日志中的错误
		_cmd = fmt.Sprintf("grep ERROR /opt/app/%s/logs/%s", service, logname)
	} else if action == "logE" {
		_cmd = fmt.Sprintf("grep --color -E 'error|ERROR|exception|Exception' /opt/app/%s/logs/%s", service, logname)
	} else if action == "loge10" {
		_cmd = fmt.Sprintf("grep -C 10 ERROR /opt/app/%s/logs/%s", service, logname)
	} else if action == "loge50" {
		_cmd = fmt.Sprintf("grep -C 50 ERROR /opt/app/%s/logs/%s", service, logname)
	} else if action == "loge200" {
		_cmd = fmt.Sprintf("grep -C 200 ERROR /opt/app/%s/logs/%s", service, logname)
	} else if action == "logen5" {
		_cmd = fmt.Sprintf("grep ERROR /opt/app/%s/logs/%s | tail -n 5", service, logname)
	} else if action == "logen10" {
		_cmd = fmt.Sprintf("grep ERROR /opt/app/%s/logs/%s | tail -n 10", service, logname)
	} else if action == "du" {
		_cmd = fmt.Sprintf("du -sh /opt/app/%s/logs/%s", service, logname)
	}
	runLinuxCmd(_cmd)

	if action == "logf" {
		logfile = fmt.Sprintf("/opt/app/%s/logs/%s", service, logname)
		tailLog(logfile)
	}
}

func servicesLogHandle(action string) {
	if action == "checklogen5" {
		lognums = "5"
	} else if action == "checklogen10" {
		lognums = "10"
	}

	//获取/opt/app下所有的服务
	getDirList("/opt/app/")
	for _, dir := range dirs {
		servicetype = existJarOrWar(dir)
		if servicetype == "jar" || servicetype == "war" {
			service = dir[9:]
			logname = findRealLogfile(service)
			_cmd = fmt.Sprintf("grep ERROR /opt/app/%s/logs/%s | tail -n %s", service, logname, lognums)
		}
		runLinuxCmd(_cmd)
	}

}

//输出帮助
func Help() {
	fmt.Println(help_content)
}

//查找系统/下大于100M的文件，即为大文件
func findBigFile() {
	_cmd = `find / -type f -size +100M  -print0 | xargs -0 du -h | sort`
	runLinuxCmd(_cmd)
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

//查看当前服务状态
//加了 服务/bin 修复查找服务时的唯一性bug
func serviceStatus(service string) {
	var result string
	service, servicetype = isJarOrWar(service)
	fmt.Println("现在查看 " + service + " 服务运行状态...\n")
	// _cmd1 = fmt.Sprintf("ps -ef | grep -w %s/conf | grep -v grep | grep -v svc", service)
	// _cmd2 = fmt.Sprintf("ps -ef | grep -w %s/bin | grep -v grep | grep -v svc", service)
	// result = runLinuxCmdWithPureReturn(_cmd1)
	// if result == "" {
	// 	runLinuxCmd(_cmd2)
	// } else {
	// 	runLinuxCmd(_cmd1)
	// }
	if servicetype != "consul" {
		_cmd = fmt.Sprintf("ps -ef | grep -w %s | grep -v grep | grep -v svc", service)
		runLinuxCmd(_cmd)

		_pid1 := getPid(service)

		_cmd1 = fmt.Sprintf("netstat -lntup | grep %s", _pid1)

		_pid2 := getPid2(service)

		_cmd2 = fmt.Sprintf("netstat -lntup | grep %s", _pid2)

		result = runLinuxCmdWithPureReturn(_cmd2)

		if result == "" {
			runLinuxCmd(_cmd1)
		} else {
			runLinuxCmd(_cmd2)
		}
	}

	if servicetype == "consul" {
		_cmd = fmt.Sprintf("ps -ef | grep %s | grep -v grep |  grep config-dir", service)
		runLinuxCmd(_cmd)
	}

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
		// 只有1个参数，比如输入svc,直接弹出help文档
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

	if action == "restart" || action == "re" {
		serviceRestart(argname)
	} else if action == "start" {
		serviceStart(argname)
	} else if action == "stop" {
		serviceStop(argname)
	} else if action == "status" || action == "st" {
		serviceStatus(argname)
	} else if action == "startall" {
		serviceStartall()
	} else if action == "stopall" {
		serviceStopall()
	} else if action == "restartall" {
		serviceRestartall()
	} else if action == "conf" {
		confService(argname)
	} else if action == ":" {
		colon(argname)
	} else if action == "cat" {
		fileCat(argname)
	} else if action == "send" {
		sendQiyeWechat(argname)
	} else if action == "logr" || action == "logo" {
		logFilter(action, argname, keyword)
	} else if action == "log" || action == "logf" || action == "loge" || action == "logE" || action == "du" {
		logHandle(action, argname)
	} else if action == "loge10" || action == "loge50" || action == "loge200" || action == "logen5" || action == "logen10" {
		logHandle(action, argname)
	} else if action == "checklogen5" || action == "checklogen10" {
		servicesLogHandle(action)
	} else if action == "check" {
		checkService()
	} else if action == "checktime" {
		checkTimeCron()
	} else if action == "ls" {
		lsService()
	} else if action == "find" {
		findBigFile()
	} else if action == "help" {
		Help()
	} else if action == "version" {
		Version()
	} else {
		Help()
	}
}
