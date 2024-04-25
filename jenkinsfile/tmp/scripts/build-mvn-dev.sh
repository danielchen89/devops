#!/usr/bin/env bash

if [[ $1 == "snapshots" ]]
then
    /data/mvn_dev/bin/mvn -Dmaven.javadoc.skip=true -Dmaven.test.skip=true clean deploy  -DaltDeploymentRepository=snapshots::default::http://10.0.100.124:8081/nexus/content/repositories/snapshots
elif [[ $1 == "releases" ]]
then
    /data/mvn_dev/bin/mvn -Dmaven.javadoc.skip=true -Dmaven.test.skip=true clean deploy  -DaltDeploymentRepository=releases::default::http://10.0.100.124:8081/nexus/content/repositories/releases
else
    echo "输入参数错误"
    exit 0
fi