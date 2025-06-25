import logging
import sys

def setup_logger():
    """로깅 설정"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('youtube_reporter.log', encoding='utf-8')
        ]
    )
    # 콘솔 출력 인코딩 설정
    import os
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    return logging.getLogger(__name__)