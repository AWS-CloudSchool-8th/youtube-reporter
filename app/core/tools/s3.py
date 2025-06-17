import boto3
import os
from mimetypes import guess_type
from config.settings import api_config
from utils.exceptions import S3UploadError
from utils.error_handler import safe_execute
from botocore.exceptions import ClientError, NoCredentialsError


def _upload_to_s3_impl(file_path: str, object_name: str = None, content_type: str = None) -> str:
    """실제 S3 업로드 로직 (내부용) - 에러 처리 강화"""
    if not os.path.exists(file_path):
        raise S3UploadError(f"File not found: {file_path}", "upload_to_s3")

    if not api_config.s3_bucket:
        raise S3UploadError("S3 bucket name not configured", "upload_to_s3")

    try:
        s3 = boto3.client("s3", region_name=api_config.aws_region)
        bucket_name = api_config.s3_bucket
        object_name = object_name or os.path.basename(file_path)
        content_type = content_type or guess_type(file_path)[0] or "application/octet-stream"

        # 먼저 버킷 접근 권한 확인
        try:
            s3.head_bucket(Bucket=bucket_name)
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                raise S3UploadError(f"Bucket '{bucket_name}' does not exist", "upload_to_s3")
            elif error_code == '403':
                raise S3UploadError(f"Access denied to bucket '{bucket_name}'. Check IAM permissions.", "upload_to_s3")
            else:
                raise S3UploadError(f"Cannot access bucket '{bucket_name}': {error_code}", "upload_to_s3")

        # 파일 업로드
        s3.upload_file(file_path, bucket_name, object_name, ExtraArgs={
            "ACL": "public-read",
            "ContentType": content_type
        })

        return f"https://{bucket_name}.s3.{api_config.aws_region}.amazonaws.com/{object_name}"

    except NoCredentialsError:
        raise S3UploadError("AWS credentials not found. Please configure AWS CLI or set environment variables.",
                            "upload_to_s3")
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'AccessDenied':
            raise S3UploadError(
                f"Access denied. Please check:\n"
                f"1. IAM user has s3:PutObject permission for bucket '{bucket_name}'\n"
                f"2. IAM user has s3:PutObjectAcl permission (for public-read ACL)\n"
                f"3. Bucket policy allows your IAM user to upload\n"
                f"Original error: {str(e)}",
                "upload_to_s3"
            )
        else:
            raise S3UploadError(f"S3 upload failed: {str(e)}", "upload_to_s3")
    except Exception as e:
        raise S3UploadError(f"Unexpected error during S3 upload: {str(e)}", "upload_to_s3")


def upload_to_s3(file_path: str, object_name: str = None, content_type: str = None) -> str:
    """안전한 S3 업로드 (에러 처리 포함)"""
    return safe_execute(
        _upload_to_s3_impl,
        file_path,
        object_name=object_name,
        content_type=content_type,
        context="upload_to_s3",
        default_return=""
    )


def test_s3_access() -> bool:
    """S3 접근 권한 테스트"""
    try:
        if not api_config.s3_bucket:
            print("❌ S3_BUCKET_NAME이 설정되지 않았습니다.")
            return False

        s3 = boto3.client("s3", region_name=api_config.aws_region)
        bucket_name = api_config.s3_bucket

        print(f"🔍 S3 버킷 '{bucket_name}' 접근 테스트 중...")

        # 버킷 존재 및 접근 권한 확인
        s3.head_bucket(Bucket=bucket_name)
        print(f"✅ 버킷 '{bucket_name}' 접근 가능")

        # 업로드 권한 테스트 (작은 테스트 파일)
        test_content = "test"
        test_key = "test-access.txt"

        s3.put_object(
            Bucket=bucket_name,
            Key=test_key,
            Body=test_content,
            ACL="public-read"
        )
        print(f"✅ 업로드 권한 확인됨")

        # 테스트 파일 삭제
        s3.delete_object(Bucket=bucket_name, Key=test_key)
        print(f"✅ S3 접근 테스트 완료")

        return True

    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            print(f"❌ 버킷 '{bucket_name}'이 존재하지 않습니다.")
        elif error_code == '403':
            print(f"❌ 버킷 '{bucket_name}'에 대한 접근 권한이 없습니다.")
            print("💡 필요한 IAM 권한:")
            print("   - s3:ListBucket")
            print("   - s3:PutObject")
            print("   - s3:PutObjectAcl")
            print("   - s3:DeleteObject")
        else:
            print(f"❌ S3 오류: {error_code} - {str(e)}")
        return False
    except NoCredentialsError:
        print("❌ AWS 자격 증명을 찾을 수 없습니다.")
        print("💡 AWS CLI 설정 또는 환경 변수를 확인하세요.")
        return False
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {str(e)}")
        return False