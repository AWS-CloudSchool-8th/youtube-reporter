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
        stage('Update Helm Values') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: "${GIT_CREDENTIALS_ID}",
                    usernameVariable: 'GIT_USERNAME',
                    passwordVariable: 'GIT_PASSWORD'
                )]) {
                    sh """
                    git config user.name "Jenkins CI"
                    git config user.email "jenkins@yourcompany.com"
                    
                    # values.yaml에서 이미지 태그 업데이트
                    sed -i 's/tag: .*/tag: ${IMAGE_TAG}/' helm/argocd/values.yaml
                    
                    # 변경사항 커밋 및 푸시
                    git add helm/argocd/values.yaml
                    git commit -m "Update image tag to ${IMAGE_TAG} [skip ci]"
                    
                    # 인증된 URL로 푸시
                    git push https://${GIT_USERNAME}:${GIT_PASSWORD}@github.com/AWS-CloudSchool-8th/youtube-reporter.git main
                    """
                }
            }
    }
}



    post {
        success {
            echo "✅ 파이프라인 성공! ArgoCD가 자동으로 배포를 시작합니다."
        }
        failure {
            echo "❌ 파이프라인 실패"

        }
    }

