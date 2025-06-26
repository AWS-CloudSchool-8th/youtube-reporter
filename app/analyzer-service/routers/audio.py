from fastapi import APIRouter, HTTPException
from app.models.audio import AudioRequest, AudioResponse
from app.services.audio_service import audio_service
from datetime import datetime

router = APIRouter(prefix="/audio", tags=["audio"])

@router.post("/generate", response_model=AudioResponse)
async def generate_audio(request: AudioRequest):
    """�ؽ�Ʈ�� Polly�� ���� ��ȯ"""
    try:
        job_id = f"audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        result = await audio_service.generate_audio(request.text, job_id, request.voice_id)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return AudioResponse(
            job_id=job_id,
            audio_info=result,
            text_length=len(request.text),
            voice_id=request.voice_id,
            generated_at=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"���� ���� ����: {str(e)}")

@router.get("/stream/{audio_id}")
async def stream_audio(audio_id: str):
    """S3���� ����� ���� ��Ʈ���� ���"""
    try:
        audio_s3_key = await audio_service.find_audio_file(audio_id)
        return await audio_service.stream_audio(audio_s3_key)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"����� ��Ʈ���� ����: {str(e)}") 