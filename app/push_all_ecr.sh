#!/bin/bash

# ECR 푸시할 서비스 목록
REPOS=("auth_service" "document_service" "youtube_service" "analyzer_service" "report_service")

# AWS 계정 ID 및 리전
AWS_ACCOUNT_ID="922805825674"  # 여기를 본인 계정 ID로 변경하세요
REGION="us-east-1"

# ECR 로그인
echo "🔐 Logging in to Amazon ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

# 각 서비스에 대해 빌드 태깅 푸시
for repo in "${REPOS[@]}"; do
  echo "📦 Processing $repo..."

  # 리포지토리 없으면 생성
  aws ecr describe-repositories --repository-names $repo --region $REGION > /dev/null 2>&1
  if [ $? -ne 0 ]; then
    echo "🆕 Creating ECR repository: $repo"
    aws ecr create-repository --repository-name $repo --region $REGION
  fi

  # 태그 및 푸시
  docker tag $repo:latest $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$repo:latest
  docker push $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$repo:latest

  echo "✅ $repo pushed to ECR."
done

echo "🎉 All images have been pushed to ECR successfully."
