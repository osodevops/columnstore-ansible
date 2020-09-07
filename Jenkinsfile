pipeline {
    agent { label 'master' }
    parameters {
        string(name: 'enterpriseToken', defaultValue: '', description: 'The MariaDB Enterprise token required to build')
        booleanParam(name: 'buildAMI', defaultValue: false, description: 'Build AMI (Packer)')
        booleanParam(name: 'provisionServers', defaultValue: false, description: 'Run Ansible Playbook')
    }
    stages {
        stage('Packer Build') {
            when {
                expression { params.buildAMI == true }
            }
            steps {
                script {
                    COMMIT = env.GIT_COMMIT
                    sh "packer validate " +
                        "-var \'COMMIT=${COMMIT}\' " +
                        "-var \'TOKEN=${enterpriseToken}\' " +
                        "packer.json"
                    sh "packer build " +
                        "-var \'COMMIT=${COMMIT}\' " +
                        "-var \'TOKEN=${enterpriseToken}\' " +
                        "packer.json"
                }
            }
        }
        stage('Provision Server') {
            when {
                expression { params.provisionServers == true }
            }
            steps {
                script {
                    dir("provision_db"){
                        sh "cp /var/lib/jenkins/.ssh/key.pem ./files/key.pem"
                        sh "ansible-playbook provision.yml "
                    }
                }
            }
        }
    }
    post {
        always {
            cleanWs()
        }
    }
}
