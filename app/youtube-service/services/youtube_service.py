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

# �α� ����
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
VIDCAP_API_KEY = os.getenv("VIDCAP_API_KEY")

class YouTubeService:
    def __init__(self):
        pass

    async def search_videos(self, query: str, max_results: int = 10) -> YouTubeSearchResponse:
        """YouTube ���� �˻�"""
        try:
            logger.info(f"YouTube �˻� ����: query={query}, max_results={max_results}")
            
            # �˻� ��û
            search_results = YoutubeSearch(
                query,
                max_results=max_results
            ).to_dict()

            logger.info(f"�˻� ��� ��: {len(search_results)}")

            # ���� ����
            videos = []
            for item in search_results:
                try:
                    # ��ȸ�� ���ڿ��� ���ڷ� ��ȯ
                    views = item.get('views', '0')
                    views = int(re.sub(r'[^\d]', '', views)) if views else 0

                    # ��� �ð� ���ڿ��� �� ������ ��ȯ
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
                        published_at=datetime.now(),  # ���� �Խ����� API���� �������� ����
                        view_count=views,
                        like_count=0,  # API���� �������� ����
                        comment_count=0,  # API���� �������� ����
                        duration=str(duration_seconds),
                        thumbnail_url=item['thumbnails'][0] if item.get('thumbnails') else ''
                    )
                    videos.append(video)
                except Exception as e:
                    logger.error(f"���� ���� ��ȯ �� ����: {str(e)}")
                    continue

            logger.info(f"���������� ��ȯ�� ���� ��: {len(videos)}")

            return YouTubeSearchResponse(
                query=query,
                total_results=len(videos),
                videos=videos,
                next_page_token=None  # API���� �������� ����
            )

        except Exception as e:
            logger.error(f"YouTube �˻� ����: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"YouTube �˻� ����: {str(e)}"
            )

    async def analyze_video(self, video_id: str, include_comments: bool = True,
                          include_transcript: bool = True, max_comments: int = 100) -> YouTubeAnalysisResponse:
        """YouTube ���� �м�"""
        try:
            logger.info(f"���� �м� ����: video_id={video_id}")
            
            # ���� ���� ��û
            search_results = YoutubeSearch(
                f"id:{video_id}",
                max_results=1
            ).to_dict()

            if not search_results:
                logger.error(f"������ ã�� �� ����: {video_id}")
                raise HTTPException(status_code=404, detail="������ ã�� �� �����ϴ�")

            item = search_results[0]
            
            # ��ȸ�� ���ڿ��� ���ڷ� ��ȯ
            views = item.get('views', '0')
            views = int(re.sub(r'[^\d]', '', views)) if views else 0

            # ��� �ð� ���ڿ��� �� ������ ��ȯ
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
                published_at=datetime.now(),  # ���� �Խ����� API���� �������� ����
                view_count=views,
                like_count=0,  # API���� �������� ����
                comment_count=0,  # API���� �������� ����
                duration=str(duration_seconds),
                thumbnail_url=item['thumbnails'][0] if item.get('thumbnails') else ''
            )

            # �⺻ �м� ���
            analysis_results = {
                "engagement_rate": 0,  # API���� �������� ����
                "comment_ratio": 0,  # API���� �������� ����
                "like_ratio": 0  # API���� �������� ����
            }

            # ��� �м� (API���� �������� ����)
            comments_analysis = None
            if include_comments:
                comments_analysis = {
                    "status": "not_available",
                    "message": "��� �м��� ���� �������� �ʽ��ϴ�"
                }

            # �ڸ� �м� (API���� �������� ����)
            transcript_analysis = None
            if include_transcript:
                transcript_analysis = {
                    "status": "not_available",
                    "message": "�ڸ� �м��� ���� �������� �ʽ��ϴ�"
                }

            logger.info(f"���� �м� �Ϸ�: {video_id}")

            return YouTubeAnalysisResponse(
                video_info=video_info,
                analysis_results=analysis_results,
                comments_analysis=comments_analysis,
                transcript_analysis=transcript_analysis,
                created_at=datetime.now(),
                completed_at=datetime.now()
            )

        except Exception as e:
            logger.error(f"���� �м� ����: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"YouTube ���� �м� ����: {str(e)}"
            )

    def extract_youtube_caption_tool(self, youtube_url: str) -> str:
        """YouTube URL���� �ڸ��� �����ϴ� �Լ� (Vidcap API Ȱ��)"""
        api_url = "https://vidcap.xyz/api/v1/youtube/caption"
        params = {"url": youtube_url, "locale": "ko"}
        headers = {"Authorization": f"Bearer {VIDCAP_API_KEY}"}
        try:
            response = requests.get(api_url, params=params, headers=headers)
            response.raise_for_status()
            return response.json().get("data", {}).get("content", "")
        except Exception as e:
            return f"�ڸ� ���� ����: {str(e)}"

youtube_service = YouTubeService() 