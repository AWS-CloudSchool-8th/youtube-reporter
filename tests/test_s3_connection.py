#!/usr/bin/env python3
"""
S3 연결 테스트 및 디버깅 스크립트
"""

import boto3
import os
import json
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

def test_s3_connection():
    """S3 연결 테스트 및 디버깅 정보 출력"""
    print("\n===== S3 연결 테스트 =====")
    
    # 환경 변수 로드
    aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    aws_region = os.getenv("AWS_REGION")
    aws_s3_bucket = os.getenv("AWS_S3_BUCKET")
    s3_bucket_name = os.getenv("S3_BUCKET_NAME", aws_s3_bucket)  # AWS_S3_BUCKET을 기본값으로 사용
    
    # 설정 정보 출력
    print(f"AWS_REGION: {aws_region}")
    print(f"AWS_S3_BUCKET: {aws_s3_bucket}")
    print(f"S3_BUCKET_NAME: {s3_bucket_name}")
    
    # AWS 자격 증명 확인 (키 자체는 보안상 출력하지 않음)
    print(f"AWS_ACCESS_KEY_ID 설정됨: {'예' if aws_access_key else '아니오'}")
    print(f"AWS_SECRET_ACCESS_KEY 설정됨: {'예' if aws_secret_key else '아니오'}")
    
    try:
        # S3 클라이언트 생성
        s3_client = boto3.client(
            's3', 
            region_name=aws_region,
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key
        )
        
        # 버킷 목록 조회
        response = s3_client.list_buckets()
        buckets = [bucket['Name'] for bucket in response['Buckets']]
        print(f"접근 가능한 S3 버킷 목록: {buckets}")
        
        # 지정된 버킷이 목록에 있는지 확인
        bucket_name = aws_s3_bucket or s3_bucket_name
        if bucket_name in buckets:
            print(f"✅ 버킷 '{bucket_name}' 접근 가능")
            
            # 테스트 파일 생성
            test_file = "s3_test_file.txt"
            with open(test_file, "w") as f:
                f.write("S3 테스트 파일")
            
            # 테스트 파일 업로드
            test_key = "test/s3_test_file.txt"
            s3_client.upload_file(
                test_file, 
                bucket_name, 
                test_key,
                ExtraArgs={"ACL": "public-read"}
            )
            os.remove(test_file)
            
            print(f"✅ 테스트 파일 업로드 성공: {test_key}")
            print(f"📂 파일 URL: https://{bucket_name}.s3.{aws_region}.amazonaws.com/{test_key}")
            
            # 버킷 내 객체 목록 조회
            objects = s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=5)
            if 'Contents' in objects:
                print(f"📁 버킷 내 최근 파일 (최대 5개):")
                for obj in objects['Contents']:
                    print(f"  - {obj['Key']} ({obj['Size']} bytes)")
            else:
                print("📁 버킷이 비어 있습니다.")
        else:
            print(f"❌ 버킷 '{bucket_name}'에 접근할 수 없습니다.")
            print(f"💡 버킷이 존재하는지, 그리고 접근 권한이 있는지 확인하세요.")
        
    except Exception as e:
        print(f"❌ S3 연결 테스트 실패: {str(e)}")
        print("💡 AWS 자격 증명과 버킷 설정을 확인하세요.")
    
    print("===== 테스트 완료 =====\n")

def test_s3_upload():
    """S3 파일 업로드 테스트"""
    print("\n===== S3 파일 업로드 테스트 =====")
    
    # 환경 변수 로드
    aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    aws_region = os.getenv("AWS_REGION")
    aws_s3_bucket = os.getenv("AWS_S3_BUCKET")
    
    try:
        # S3 클라이언트 생성
        s3_client = boto3.client(
            's3', 
            region_name=aws_region,
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key
        )
        
        # 테스트 JSON 데이터 생성
        test_data = {
            "title": "테스트 보고서",
            "sections": [
                {"type": "paragraph", "content": "이것은 테스트 보고서입니다."},
                {"type": "paragraph", "content": "S3 업로드 테스트를 위한 내용입니다."}
            ],
            "timestamp": "2023-07-01T12:00:00Z"
        }
        
        # JSON 파일로 저장
        test_file = "test_report.json"
        with open(test_file, "w", encoding="utf-8") as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)
        
        # 파일 업로드
        test_key = f"test/test_report_{os.urandom(4).hex()}.json"
        s3_client.upload_file(
            test_file, 
            aws_s3_bucket, 
            test_key,
            ExtraArgs={
                "ACL": "public-read",
                "ContentType": "application/json"
            }
        )
        os.remove(test_file)
        
        print(f"✅ JSON 파일 업로드 성공: {test_key}")
        print(f"📂 파일 URL: https://{aws_s3_bucket}.s3.{aws_region}.amazonaws.com/{test_key}")
        
    except Exception as e:
        print(f"❌ S3 업로드 테스트 실패: {str(e)}")
    
    print("===== 테스트 완료 =====\n")

if __name__ == "__main__":
    test_s3_connection()
    test_s3_upload()