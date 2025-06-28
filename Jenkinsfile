pipeline {
    agent any

    environment {
        AWS_REGION = 'us-west-2'  // 사용 중인 리전
        ECR_REPO = '492021314651.dkr.ecr.us-west-2.amazonaws.com/youtube-reporter-app'
        IMAGE_TAG = "build-${BUILD_NUMBER}"
        GIT_REPO = 'https://github.com/AWS-CloudSchool-8th/youtube-reporter.git'
        GIT_CREDENTIALS_ID = 'git_cre'
        AWS_CREDENTIALS_ID = 'aws_cre'  // IAM 인증 연결 (Jenkins Credential에 등록된 이름- 지형aws로함.)
    }

    stages {
        stage('Clone Repository') {
            steps {
                checkout([$class: 'GitSCM',
                    branches: [[name: '*/main']],
                    userRemoteConfigs: [[
                        url: "${GIT_REPO}",
                        credentialsId: "${GIT_CREDENTIALS_ID}"
                    ]]
                ])
            }
        }

        stage('Docker Build') {
            steps {
                sh """
                docker build -t ${ECR_REPO}:${IMAGE_TAG} .
                docker tag ${ECR_REPO}:${IMAGE_TAG} ${ECR_REPO}:latest
                """
            }
        }

        stage('Push to ECR') {
            steps {
                withCredentials([[
                    $class: 'AmazonWebServicesCredentialsBinding',
                    credentialsId: "${AWS_CREDENTIALS_ID}"
                ]]) {
                    sh """
                    aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REPO}
                    docker push ${ECR_REPO}:${IMAGE_TAG}
                    docker push ${ECR_REPO}:latest
                    docker image rm ${ECR_REPO}:${IMAGE_TAG}
                    docker image rm ${ECR_REPO}:latest
                    """
                }
            }
        }
    }
}
