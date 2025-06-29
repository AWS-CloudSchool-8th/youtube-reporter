from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from services.s3_service import s3_service
from shared_lib.core.config import settings
import json

router = APIRouter(
    prefix="/reports",
    tags=["reports"]
)

@router.get("/list")
async def list_reports() -> List[Dict[str, Any]]:
    try:
        objects = s3_service.list_objects(prefix="reports/", max_keys=100)
        
        reports = []
        for obj in objects:
            if not obj.get("Key", "").endswith(".json"):
                continue
                
            key = obj.get("Key", "")
            last_modified = obj.get("LastModified")
            size = obj.get("Size", 0)
            
            url = f"https://{s3_service.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"
            
            metadata = {}
            try:
                metadata_key = key.replace("reports/", "metadata/").replace("_report.json", "_metadata.json")
                metadata_objects = s3_service.list_objects(prefix=metadata_key, max_keys=1)
                
                if metadata_objects:
                    metadata_url = f"https://{s3_service.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{metadata_key}"
                    metadata = {"url": metadata_url}
            except Exception as e:
                print(f"file: {e}")
            
            # ������ ���� �߰�
            reports.append({
                "key": key,
                "title": extract_title_from_key(key),
                "last_modified": last_modified.isoformat() if hasattr(last_modified, "isoformat") else str(last_modified),
                "size": size,
                "url": url,
                "metadata": metadata,
                "type": "YouTube"
            })
        
        reports.sort(key=lambda x: x.get("last_modified", ""), reverse=True)
        
        return reports
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"file: {str(e)}")

@router.get("/{report_id}")
async def get_report(report_id: str) -> Dict[str, Any]:
    try:
        key = f"reports/{report_id}_report.json"
        
        objects = s3_service.list_objects(prefix=key, max_keys=1)
        if not objects:
            raise HTTPException(status_code=404, detail=f"file: {report_id}")
        
        url = f"https://{s3_service.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"
        
        metadata = {}
        try:
            metadata_key = f"metadata/{report_id}_metadata.json"
            metadata_objects = s3_service.list_objects(prefix=metadata_key, max_keys=1)
            
            if metadata_objects:
                metadata_url = f"https://{s3_service.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{metadata_key}"
                metadata = {"url": metadata_url}
        except Exception as e:
            print(f"file: {e}")
        
        return {
            "report_id": report_id,
            "url": url,
            "metadata": metadata
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"file: {str(e)}")

def extract_title_from_key(key: str) -> str:
    if not key:
        return "no title"
    
    file_name = key.split("/")[-1]
    
    name_without_ext = file_name.replace(".json", "")
    
    clean_name = name_without_ext\
        .replace("_report", "")\
        .replace("report_", "")\
        .replace("_metadata", "")
    
    import re
    uuid_pattern = r"[0-9a-f]{8}[-_][0-9a-f]{4}[-_][0-9a-f]{4}[-_][0-9a-f]{4}[-_][0-9a-f]{12}"
    clean_name = re.sub(uuid_pattern, "", clean_name, flags=re.IGNORECASE)
    
    result = clean_name.replace("_", " ").strip()
    
    return result if result else "no file"
