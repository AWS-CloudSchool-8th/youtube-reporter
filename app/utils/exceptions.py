"""YouTube Reporter 프로젝트 전용 예외 클래스들"""

class YouTubeReporterError(Exception):
    """기본 예외 클래스"""
    def __init__(self, message: str, context: str = None):
        self.message = message
        self.context = context
        super().__init__(self.message)

class CaptionError(YouTubeReporterError):
    """자막 추출 실패"""
    pass

class ReportGenerationError(YouTubeReporterError):
    """보고서 생성 실패"""
    pass

class VisualSplitError(YouTubeReporterError):
    """시각화 블록 분할 실패"""
    pass

class VisualizationError(YouTubeReporterError):
    """시각화 생성 실패"""
    pass

class CodeExecutionError(YouTubeReporterError):
    """코드 실행 실패"""
    pass

class S3UploadError(YouTubeReporterError):
    """S3 업로드 실패"""
    pass