FROM centos:7

# 处理yum源地址
RUN yum -y install wget
RUN wget -O /etc/yum.repos.d/CentOS-Base.repo http://mirrors.aliyun.com/repo/Centos-7.repo
RUN wget -O /etc/yum.repos.d/epel.repo http://mirrors.aliyun.com/repo/epel-7.repo

# 安装依赖
RUN yum -y install openssl openssl-devel sudo java-1.8.0-openjdk git ca-certificates curl mercurial procps unzip ntp

# 设置系统时间为上海时间
COPY Shanghai /etc/localtime

#安装python3
RUN yum -y install python3 python3-pip
RUN pip3 install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple/
RUN pip3 install oss2 fabric3 requests -i https://pypi.tuna.tsinghua.edu.cn/simple/ 
#安装docker
RUN yum -y install docker

ARG user=jenkins
ARG group=jenkins
ARG uid=1000
ARG gid=1000

#安装sonar-scanner
RUN cd /usr/local \
&& wget https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-4.6.2.2472.zip \
&& unzip sonar-scanner-cli-4.6.2.2472.zip && mv sonar-scanner-4.6.2.2472 sonar-scanner \
&& ln -s /usr/local/sonar-scanner/bin/sonar-scanner /usr/local/bin/sonar-scanner

RUN groupadd -g ${gid} ${group}
RUN useradd -c "Jenkins user" -d /home/${user} -u ${uid} -g ${gid} -m ${user}
LABEL Description="This is a base image, which provides the Jenkins agent executable (slave.jar)"

ARG AGENT_WORKDIR=/home/${user}/agent
ARG JENKINS_WORKDIR=/var/lib/${user}
RUN curl --create-dirs -sSLo /usr/share/jenkins/slave.jar https://repo.jenkins-ci.org/public/org/jenkins-ci/main/remoting/3.16/remoting-3.16.jar \
  && chmod 755 /usr/share/jenkins
RUN curl --create-dirs -sSLo /usr/local/bin/jenkins-slave https://raw.githubusercontent.com/jenkinsci/docker-jnlp-slave/3.27-1/jenkins-slave \
        && chmod a+x /usr/local/bin/jenkins-slave

ENV AGENT_WORKDIR=${AGENT_WORKDIR}
RUN mkdir /home/${user}/.jenkins && mkdir -p ${AGENT_WORKDIR}
RUN mkdir -p ${JENKINS_WORKDIR}
ENV PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/root/bin
VOLUME /home/${user}/.jenkins
VOLUME ${AGENT_WORKDIR}
WORKDIR ${JENKINS_WORKDIR}

#下面的用户不加就能root启动
USER ${user}
ENTRYPOINT ["jenkins-slave"]