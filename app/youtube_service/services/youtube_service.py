from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import HTTPException
from shared_lib.models.youtube import YouTubeVideoInfo, YouTubeSearchResponse, YouTubeAnalysisResponse
from youtube_search import YoutubeSearch
import re
import logging
import requests
import os
from dotenv import load_dotenv

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
VIDCAP_API_KEY = os.getenv("VIDCAP_API_KEY")

class YouTubeService:
    def __init__(self):
        pass

    async def search_videos(self, query: str, max_results: int = 10) -> YouTubeSearchResponse:
        """Search YouTube videos"""
        try:
            logger.info(f"Start YouTube search: query={query}, max_results={max_results}")
            
            search_results = YoutubeSearch(
                query,
                max_results=max_results
            ).to_dict()

            logger.info(f"Number of results: {len(search_results)}")

            videos = []
            for item in search_results:
                try:
                    views = item.get('views', '0')
                    views = int(re.sub(r'[^\d]', '', views)) if views else 0

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
                        published_at=datetime.now(),  # Publish date not available
                        view_count=views,
                        like_count=0,
                        comment_count=0,
                        duration=str(duration_seconds),
                        thumbnail_url=item['thumbnails'][0] if item.get('thumbnails') else ''
                    )
                    videos.append(video)
                except Exception as e:
                    logger.error(f"Error converting video info: {str(e)}")
                    continue

            logger.info(f"Successfully converted videos: {len(videos)}")

            return YouTubeSearchResponse(
                query=query,
                total_results=len(videos),
                videos=videos,
                next_page_token=None
            )

        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"YouTube search failed: {str(e)}"
            )

    async def analyze_video(self, video_id: str, include_comments: bool = True,
                            include_transcript: bool = True, max_comments: int = 100) -> YouTubeAnalysisResponse:
        """Analyze YouTube video"""
        try:
            logger.info(f"Start video analysis: video_id={video_id}")
            
            search_results = YoutubeSearch(
                f"id:{video_id}",
                max_results=1
            ).to_dict()

            if not search_results:
                logger.error(f"Video not found: {video_id}")
                raise HTTPException(status_code=404, detail="Video not found")

            item = search_results[0]
            
            views = item.get('views', '0')
            views = int(re.sub(r'[^\d]', '', views)) if views else 0

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
                published_at=datetime.now(),
                view_count=views,
                like_count=0,
                comment_count=0,
                duration=str(duration_seconds),
                thumbnail_url=item['thumbnails'][0] if item.get('thumbnails') else ''
            )

            analysis_results = {
                "engagement_rate": 0,
                "comment_ratio": 0,
                "like_ratio": 0
            }

            comments_analysis = None
            if include_comments:
                comments_analysis = {
                    "status": "not_available",
                    "message": "Comment analysis is not supported"
                }

            transcript_analysis = None
            if include_transcript:
                transcript_analysis = {
                    "status": "not_available",
                    "message": "Transcript analysis is not supported"
                }

            logger.info(f"Video analysis complete: {video_id}")

            return YouTubeAnalysisResponse(
                video_info=video_info,
                analysis_results=analysis_results,
                comments_analysis=comments_analysis,
                transcript_analysis=transcript_analysis,
                created_at=datetime.now(),
                completed_at=datetime.now()
            )

        except Exception as e:
            logger.error(f"Video analysis failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"YouTube video analysis failed: {str(e)}"
            )

    def extract_youtube_caption_tool(self, youtube_url: str) -> str:
        """Extract YouTube captions using Vidcap API"""
        api_url = "https://vidcap.xyz/api/v1/youtube/caption"
        params = {"url": youtube_url, "locale": "ko"}
        headers = {"Authorization": f"Bearer {VIDCAP_API_KEY}"}
        try:
            response = requests.get(api_url, params=params, headers=headers)
            response.raise_for_status()
            return response.json().get("data", {}).get("content", "")
        except Exception as e:
            return f"Failed to extract captions: {str(e)}"

youtube_service = YouTubeService()
