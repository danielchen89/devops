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
