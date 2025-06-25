from typing import Dict, Any
from ..agents.graph_workflow import GraphWorkflow

class LangGraphService:
    def __init__(self):
        self.workflow = GraphWorkflow()
    
    def run_graph(self, youtube_url: str) -> Dict[str, Any]:
        """그래프 실행"""
        return self.workflow.run(youtube_url)