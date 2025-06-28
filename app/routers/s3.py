from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Dict, Any, List, Optional
from app.services.user_s3_service import user_s3_service
from app.core.config import settings
from app.core.auth import get_current_user
import json

router = APIRouter(
    prefix="/s3",
    tags=["s3"]
)

@router.get("/list")
async def list_s3_objects(
    prefix: str = Query("", description="S3 객체 경로 접두사"),
    max_keys: int = Query(100, description="최대 객체 수")
) -> Dict[str, Any]:
    """
    S3 버킷 내 객체 목록 조회
    
    - **prefix**: 객체 경로 접두사 (예: 'reports/')
    - **max_keys**: 최대 객체 수
    """
    try:
        response = user_s3_service.s3_client.list_objects_v2(
            Bucket=user_s3_service.bucket_name,
            Prefix=prefix,
            MaxKeys=max_keys
        )
        
        objects = []
        if 'Contents' in response:
            for obj in response['Contents']:
                objects.append({
                    "Key": obj.get("Key", ""),
                    "Size": obj.get("Size", 0),
                    "LastModified": obj.get("LastModified", "").isoformat() if hasattr(obj.get("LastModified", ""), "isoformat") else obj.get("LastModified", ""),
                    "ETag": obj.get("ETag", ""),
                    "StorageClass": obj.get("StorageClass", "")
                })
        
        return {
            "bucket": user_s3_service.bucket_name,
            "region": settings.AWS_REGION,
            "prefix": prefix,
            "objects": objects
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"S3 객체 목록 조회 실패: {str(e)}")

@router.get("/object/{key:path}")
async def get_s3_object(key: str) -> Dict[str, Any]:
    """
    S3 객체 정보 조회
    
    - **key**: 객체 키 (경로)
    """
    try:
        # S3 객체 헤더 조회
        response = user_s3_service.s3_client.head_object(
            Bucket=user_s3_service.bucket_name,
            Key=key
        )
        
        # 미리 서명된 URL 생성
        url = user_s3_service.get_presigned_url(key)
        
        return {
            "key": key,
            "size": response.get("ContentLength", 0),
            "last_modified": response.get("LastModified", "").isoformat() if hasattr(response.get("LastModified", ""), "isoformat") else response.get("LastModified", ""),
            "content_type": response.get("ContentType", ""),
            "metadata": response.get("Metadata", {}),
            "url": url
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"S3 객체를 찾을 수 없음: {str(e)}")

@router.get("/reports/list")
async def list_reports_with_metadata(current_user: dict = Depends(get_current_user)) -> List[Dict[str, Any]]:
    """
    보고서 목록 조회 (메타데이터 포함, 사용자별)
    """
    try:
        user_id = current_user["user_id"]
        
        # 사용자별 보고서 파일 목록 가져오기 (올바른 경로 사용)
        prefix = f"users/{user_id}/reports/"
        
        response = user_s3_service.s3_client.list_objects_v2(
            Bucket=user_s3_service.bucket_name,
            Prefix=prefix,
            MaxKeys=100
        )
        
        reports = []
        
        if 'Contents' not in response:
            return reports
            
        for obj in response['Contents']:
            if obj.get("Key", "").endswith("_report.json"):
                try:
                    # 보고서 파일 내용 가져오기
                    report_content = user_s3_service.get_file_content(obj.get("Key", ""))
                    if report_content:
                        report_data = json.loads(report_content)
                        
                        # job_id 추출
                        job_id = obj.get("Key", "").replace(prefix, "").replace("_report.json", "")
                        
                        # 메타데이터 파일 가져오기
                        metadata_key = f"metadata/{user_id}/{job_id}_metadata.json"
                        metadata = {}
                        
                        try:
                            metadata_content = user_s3_service.get_file_content(metadata_key)
                            if metadata_content:
                                metadata = json.loads(metadata_content)
                        except:
                            # 메타데이터가 없어도 계속 진행
                            pass
                        
                        # 미리 서명된 URL 생성
                        report_url = user_s3_service.get_presigned_url(obj.get("Key", ""))
                        
                        # 보고서 데이터에서 제목 추출 시도
                        title = metadata.get("youtube_title", "")
                        if not title and report_data.get("report"):
                            title = report_data["report"].get("title", f"Report {job_id}")
                        if not title:
                            title = f"Report {job_id}"
                        
                        reports.append({
                            "id": job_id,
                            "key": obj.get("Key", ""),
                            "title": title,
                            "youtube_url": metadata.get("youtube_url", ""),
                            "youtube_channel": metadata.get("youtube_channel", "Unknown Channel"),
                            "youtube_duration": metadata.get("youtube_duration", "Unknown"),
                            "youtube_thumbnail": metadata.get("youtube_thumbnail", ""),
                            "type": "YouTube",
                            "last_modified": obj.get("LastModified", "").isoformat() if hasattr(obj.get("LastModified", ""), "isoformat") else obj.get("LastModified", ""),
                            "url": report_url,
                            "reportUrl": report_url,
                            "hasAudio": False,  # TODO: 오디오 파일 존재 여부 확인
                            "metadata": metadata
                        })
                        
                except Exception as e:
                    print(f"보고서 처리 실패: {obj.get('Key', '')} - {e}")
                    continue
        
        # 최신순 정렬
        reports.sort(key=lambda x: x.get("last_modified", ""), reverse=True)
        
        return reports
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"보고서 목록 조회 실패: {str(e)}")