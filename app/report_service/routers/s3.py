from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Dict, Any, List, Optional
from services.s3_service import s3_service
from shared_lib.core.config import settings
from shared_lib.core.auth import get_current_user
import json

router = APIRouter(
    prefix="/s3",
    tags=["s3"]
)

@router.get("/list")
async def list_s3_objects(
    prefix: str = Query("", description="S3"),
    max_keys: int = Query(100, description="s3 list")
) -> Dict[str, Any]:
    try:
        objects = s3_service.list_objects(prefix=prefix, max_keys=max_keys)
        
        return {
            "bucket": s3_service.bucket_name,
            "region": settings.AWS_REGION,
            "prefix": prefix,
            "objects": [
                {
                    "Key": obj.get("Key", ""),
                    "Size": obj.get("Size", 0),
                    "LastModified": obj.get("LastModified", "").isoformat() if hasattr(obj.get("LastModified", ""), "isoformat") else obj.get("LastModified", ""),
                    "ETag": obj.get("ETag", ""),
                    "StorageClass": obj.get("StorageClass", "")
                }
                for obj in objects
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"S3: {str(e)}")

@router.get("/object/{key:path}")
async def get_s3_object(key: str) -> Dict[str, Any]:
    try:
        response = s3_service.s3_client.head_object(
            Bucket=s3_service.bucket_name,
            Key=key
        )
        
        url = s3_service.s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': s3_service.bucket_name, 'Key': key},
            ExpiresIn=3600
        )
        
        return {
            "key": key,
            "size": response.get("ContentLength", 0),
            "last_modified": response.get("LastModified", "").isoformat() if hasattr(response.get("LastModified", ""), "isoformat") else response.get("LastModified", ""),
            "content_type": response.get("ContentType", ""),
            "metadata": response.get("Metadata", {}),
            "url": url
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"S3 : {str(e)}")

@router.get("/reports/list")
async def list_reports_with_metadata(current_user: dict = Depends(get_current_user)) -> List[Dict[str, Any]]:
    try:
        user_id = current_user["user_id"]
        report_objects = s3_service.list_objects(prefix=f"reports/{user_id}/", max_keys=100)
        
        reports = []
        for obj in report_objects:
            if obj.get("Key", "").endswith("_report.json"):
                try:
                    report_content = s3_service.get_file_content(obj.get("Key", ""))
                    if report_content:
                        report_data = json.loads(report_content)
                        
                        job_id = obj.get("Key", "").replace(f"reports/{user_id}/", "").replace("_report.json", "")
                        
                        metadata_key = f"metadata/{user_id}/{job_id}_metadata.json"
                        metadata_content = s3_service.get_file_content(metadata_key)
                        metadata = {}
                        
                        if metadata_content:
                            try:
                                metadata = json.loads(metadata_content)
                            except:
                                pass
                        
                        report_url = s3_service.s3_client.generate_presigned_url(
                            'get_object',
                            Params={'Bucket': s3_service.bucket_name, 'Key': obj.get("Key", "")},
                            ExpiresIn=3600
                        )
                        
                        reports.append({
                            "id": job_id,
                            "key": obj.get("Key", ""),
                            "title": metadata.get("youtube_title", f"Report {job_id}"),
                            "youtube_url": metadata.get("youtube_url", ""),
                            "youtube_channel": metadata.get("youtube_channel", "Unknown Channel"),
                            "youtube_duration": metadata.get("youtube_duration", "Unknown"),
                            "youtube_thumbnail": metadata.get("youtube_thumbnail", ""),
                            "type": "YouTube",
                            "last_modified": obj.get("LastModified", "").isoformat() if hasattr(obj.get("LastModified", ""), "isoformat") else obj.get("LastModified", ""),
                            "url": report_url,
                            "metadata": metadata
                        })
                        
                except Exception as e:
                    print(f"file: {obj.get('Key', '')} - {e}")
                    continue
        
        reports.sort(key=lambda x: x.get("last_modified", ""), reverse=True)
        
        return reports
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"file: {str(e)}")
