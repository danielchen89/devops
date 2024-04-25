pipeline {
   agent { label 'jnlp-slave' }
   environment {
       JAVA_HOME = "/data/jdk1.8.0_101"
   } 
   stages {
		stage("1st stage") {
            steps {
                script {
				   wrap([$class: 'BuildUser']) {
					   currentBuild.displayName = "#$BUILD_NUMBER  $project  $branch  ${BUILD_USER}"
                   }
                    
                } 
            }
        }
		stage('Clean') {
			steps {
				sh '''
					/usr/bin/python3 /data/scripts/cleanWorkdir.py
				'''
			}
		}
   		stage('Clone') {
			steps {
				script{
					git([url: "git@qygit.ipaylinks.com:${project}.git", branch: env.branch])					
				}					
			}
		}

		stage('Build') {
			steps {
				sh '''
					/usr/bin/python3 /data/scripts/jenkins.py "git@qygit.ipaylinks.com:${project}.git" $branch dev
				'''
			}
		}
	}
}