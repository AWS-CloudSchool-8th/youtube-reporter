from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import HTTPException
from app.models.youtube import YouTubeVideoInfo, YouTubeSearchResponse, YouTubeAnalysisResponse
from youtube_search import YoutubeSearch
import re
import logging
import requests
import os
from dotenv import load_dotenv

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
VIDCAP_API_KEY = os.getenv("VIDCAP_API_KEY")

class YouTubeService:
    def __init__(self):
        pass

    async def search_videos(self, query: str, max_results: int = 10) -> YouTubeSearchResponse:
        """YouTube 비디오 검색"""
        try:
            logger.info(f"YouTube 검색 시작: query={query}, max_results={max_results}")
            
            # 검색 요청
            search_results = YoutubeSearch(
                query,
                max_results=max_results
            ).to_dict()

            logger.info(f"검색 결과 수: {len(search_results)}")

            # 응답 생성
            videos = []
            for item in search_results:
                try:
                    # 조회수 문자열을 숫자로 변환
                    views = item.get('views', '0')
                    views = int(re.sub(r'[^\d]', '', views)) if views else 0

                    # 재생 시간 문자열을 초 단위로 변환
                    duration = item.get('duration', '0:00')
                    duration_seconds = 0
                    
                    if duration and ':' in duration:
                        try:
                            duration_parts = duration.split(':')
                            if len(duration_parts) == 2:  # MM:SS
                                minutes, seconds = map(int, duration_parts)
                                duration_seconds = minutes * 60 + seconds
                            elif len(duration_parts) == 3:  # HH:MM:SS
                                hours, minutes, seconds = map(int, duration_parts)
                                duration_seconds = hours * 3600 + minutes * 60 + seconds
                        except ValueError:
                            duration_seconds = 0

                    video = YouTubeVideoInfo(
                        video_id=item['id'],
                        title=item['title'],
                        description=item.get('description', ''),
                        channel_title=item['channel'],
                        published_at=datetime.now(),  # 실제 게시일은 API에서 제공하지 않음
                        view_count=views,
                        like_count=0,  # API에서 제공하지 않음
                        comment_count=0,  # API에서 제공하지 않음
                        duration=str(duration_seconds),
                        thumbnail_url=item['thumbnails'][0] if item.get('thumbnails') else ''
                    )
                    videos.append(video)
                except Exception as e:
                    logger.error(f"비디오 정보 변환 중 오류: {str(e)}")
                    continue

            logger.info(f"성공적으로 변환된 비디오 수: {len(videos)}")

            return YouTubeSearchResponse(
                query=query,
                total_results=len(videos),
                videos=videos,
                next_page_token=None  # API에서 제공하지 않음
            )

        except Exception as e:
            logger.error(f"YouTube 검색 실패: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"YouTube 검색 실패: {str(e)}"
            )

    async def analyze_video(self, video_id: str, include_comments: bool = True,
                          include_transcript: bool = True, max_comments: int = 100) -> YouTubeAnalysisResponse:
        """YouTube 비디오 분석"""
        try:
            logger.info(f"비디오 분석 시작: video_id={video_id}")
            
            # 비디오 정보 요청
            search_results = YoutubeSearch(
                f"id:{video_id}",
                max_results=1
            ).to_dict()

            if not search_results:
                logger.error(f"비디오를 찾을 수 없음: {video_id}")
                raise HTTPException(status_code=404, detail="비디오를 찾을 수 없습니다")

            item = search_results[0]
            
            # 조회수 문자열을 숫자로 변환
            views = item.get('views', '0')
            views = int(re.sub(r'[^\d]', '', views)) if views else 0

            # 재생 시간 문자열을 초 단위로 변환
            duration = item.get('duration', '0:00')
            duration_parts = duration.split(':')
            if len(duration_parts) == 2:
                minutes, seconds = map(int, duration_parts)
                duration_seconds = minutes * 60 + seconds
            else:
                duration_seconds = 0

            video_info = YouTubeVideoInfo(
                video_id=item['id'],
                title=item['title'],
                description=item.get('description', ''),
                channel_title=item['channel'],
                published_at=datetime.now(),  # 실제 게시일은 API에서 제공하지 않음
                view_count=views,
                like_count=0,  # API에서 제공하지 않음
                comment_count=0,  # API에서 제공하지 않음
                duration=str(duration_seconds),
                thumbnail_url=item['thumbnails'][0] if item.get('thumbnails') else ''
            )

            # 기본 분석 결과
            analysis_results = {
                "engagement_rate": 0,  # API에서 제공하지 않음
                "comment_ratio": 0,  # API에서 제공하지 않음
                "like_ratio": 0  # API에서 제공하지 않음
            }

            # 댓글 분석 (API에서 제공하지 않음)
            comments_analysis = None
            if include_comments:
                comments_analysis = {
                    "status": "not_available",
                    "message": "댓글 분석은 현재 지원되지 않습니다"
                }

            # 자막 분석 (API에서 제공하지 않음)
            transcript_analysis = None
            if include_transcript:
                transcript_analysis = {
                    "status": "not_available",
                    "message": "자막 분석은 현재 지원되지 않습니다"
                }

            logger.info(f"비디오 분석 완료: {video_id}")

            return YouTubeAnalysisResponse(
                video_info=video_info,
                analysis_results=analysis_results,
                comments_analysis=comments_analysis,
                transcript_analysis=transcript_analysis,
                created_at=datetime.now(),
                completed_at=datetime.now()
            )

        except Exception as e:
            logger.error(f"비디오 분석 실패: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"YouTube 비디오 분석 실패: {str(e)}"
            )

    def extract_youtube_caption_tool(self, youtube_url: str) -> str:
        """YouTube URL에서 자막을 추출하는 함수 (Vidcap API 활용)"""
        api_url = "https://vidcap.xyz/api/v1/youtube/caption"
        params = {"url": youtube_url, "locale": "ko"}
        headers = {"Authorization": f"Bearer {VIDCAP_API_KEY}"}
        try:
            response = requests.get(api_url, params=params, headers=headers)
            response.raise_for_status()
            return response.json().get("data", {}).get("content", "")
        except Exception as e:
            return f"자막 추출 실패: {str(e)}"

youtube_service = YouTubeService() 