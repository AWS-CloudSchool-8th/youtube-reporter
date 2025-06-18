# services/smart_visualization_service.py - 실제 내용 반영 버전
from langchain_core.prompts import ChatPromptTemplate
from utils.llm_factory import create_llm
import json
import re
from typing import List, Dict


class SmartVisualizationService:
    def __init__(self):
        self.llm = create_llm()
        self._setup_content_aware_prompts()

    def _setup_content_aware_prompts(self):
        """실제 영상 내용을 반영하는 프롬프트"""

        self.generation_prompt = ChatPromptTemplate.from_messages([
            ("system", """
당신은 YouTube 영상 내용을 분석하여 정확한 시각화를 만드는 전문가입니다.

🔑 핵심 원칙:
1. 반드시 주어진 영상의 실제 내용만 사용하세요
2. 다른 주제의 내용을 절대 사용하지 마세요  
3. 영상에 나오지 않은 정보는 추가하지 마세요
4. 구체적이고 실제적인 정보만 포함하세요

⚠️ 절대 금지:
- 템플릿 텍스트 ("세부1", "항목1" 등)
- 다른 주제 내용 혼입
- 일반론적 표현 ("핵심 주제" 등)
- 영상과 관련없는 내용

✅ 반드시 지킬 것:
- 영상의 핵심 주제를 정확히 파악
- 영상에서 언급된 구체적 정보만 사용
- 학습자가 이해하기 쉬운 구조로 정리

현재 영상 주제: {topic}
요청 시각화: {viz_type}

영상 내용을 바탕으로 {viz_type} 시각화를 JSON 형식으로 생성하세요.
            """),
            ("human", "영상 주제: {topic}\n\n영상 내용:\n{content}\n\n특별 지시: 위 영상 내용에서만 정보를 추출하여 {viz_type} 시각화를 생성하세요.")
        ])

    async def analyze_and_generate_visualizations(self, caption: str, report_text: str) -> List[Dict]:
        """실제 영상 내용 기반 시각화 생성"""

        # 🔑 실제 주제 추출 (하드코딩 방지)
        actual_topic = self._extract_actual_topic(report_text, caption)
        print(f"🎯 실제 영상 주제: {actual_topic}")

        # 실제 내용 기반 섹션 분할
        sections = self._analyze_content_sections(report_text, caption)

        visualizations = []
        position = 0

        # 제목 섹션
        visualizations.append({
            "type": "paragraph",
            "title": "",
            "content": f"제목: {actual_topic}",
            "position": position
        })
        position += 1

        for section in sections:
            # 텍스트 섹션
            visualizations.append({
                "type": "paragraph",
                "title": section["title"],
                "content": section["content"],
                "position": position
            })
            position += 1

            # 🔑 실제 내용 기반 시각화 생성
            viz_type = self._determine_appropriate_visualization(section, actual_topic)
            if viz_type:
                viz_data = await self._generate_content_specific_visualization(
                    viz_type, actual_topic, section, caption
                )
                if viz_data and self._validate_content_accuracy(viz_data, actual_topic):
                    viz_data["position"] = position
                    visualizations.append(viz_data)
                    position += 1
                    print(f"✅ {actual_topic} 기반 {viz_type} 생성 완료")
                else:
                    print(f"❌ {viz_type} 내용 정확성 검증 실패")

        return visualizations

    def _extract_actual_topic(self, report_text: str, caption: str) -> str:
        """실제 영상 주제 정확히 추출"""

        # 제목에서 추출 시도
        lines = report_text.split('\n')
        for line in lines:
            if '제목:' in line:
                topic = line.replace('제목:', '').strip()
                if len(topic) > 5:  # 의미있는 제목인지 확인
                    return topic

        # 자막에서 핵심 키워드 추출
        caption_words = re.findall(r'[가-힣]{2,}', caption[:500])  # 처음 500자에서 키워드 추출
        word_count = {}
        for word in caption_words:
            if len(word) >= 3:  # 3글자 이상 단어만
                word_count[word] = word_count.get(word, 0) + 1

        # 가장 빈번한 단어들로 주제 구성
        if word_count:
            top_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)[:3]
            topic_keywords = [word for word, count in top_words if count >= 2]
            if topic_keywords:
                return ' '.join(topic_keywords[:2])  # 상위 2개 키워드 조합

        # 마지막 수단: 보고서 첫 문장
        first_sentence = report_text.split('.')[0].strip()
        if len(first_sentence) < 100:
            return first_sentence

        return "영상 내용 분석"

    def _analyze_content_sections(self, report_text: str, caption: str) -> List[Dict]:
        """내용 기반 섹션 분석"""
        sections = []

        # 보고서를 의미 단위로 분할
        paragraphs = re.split(r'\n\s*\n|\d+\.\s+', report_text)

        current_section = {"title": "요약", "content": ""}

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # 섹션 제목 감지 (좀 더 정확하게)
            if (len(para) < 50 and
                    any(keyword in para for keyword in ['요약', '주요', '내용', '과정', '방법', '결론', '의의', '원리', '공식'])):

                if current_section["content"]:
                    sections.append(current_section)

                # 제목에서 콜론 제거하고 정리
                title = para.replace(':', '').strip()
                current_section = {"title": title, "content": ""}
            else:
                current_section["content"] += para + " "

        if current_section["content"]:
            sections.append(current_section)

        # 중복 제거 및 정리
        unique_sections = []
        seen_content = set()

        for section in sections:
            content_key = section["content"][:100]  # 처음 100자로 중복 체크
            if content_key not in seen_content and len(section["content"]) > 20:
                seen_content.add(content_key)
                unique_sections.append(section)

        return unique_sections[:4]  # 최대 4개 섹션

    def _determine_appropriate_visualization(self, section: Dict, topic: str) -> str:
        """실제 내용에 적합한 시각화 타입 결정"""
        content = section["content"].lower()
        title = section["title"].lower()
        topic_lower = topic.lower()

        # 주제별 특화 시각화 선택
        if any(word in topic_lower for word in ['공식', '수학', '계산', '알고리즘']):
            if any(word in content for word in ['단계', '과정', '방법', '절차']):
                return "flowchart"
            elif any(word in content for word in ['구성', '요소', '원리']):
                return "mindmap"

        elif any(word in topic_lower for word in ['역사', '발전', '변화']):
            return "timeline"

        elif any(word in content for word in ['비교', '차이', '종류', 'vs']):
            return "comparison"

        elif any(word in content for word in ['구조', '분류', '계층', '체계']):
            return "tree"

        elif any(word in content for word in ['개념', '관계', '연결', '요소']):
            return "mindmap"

        elif any(word in content for word in ['과정', '단계', '방법', '절차', '순서']):
            return "flowchart"

        return None

    async def _generate_content_specific_visualization(self, viz_type: str, topic: str, section: Dict,
                                                       caption: str) -> Dict:
        """실제 내용에 특화된 시각화 생성"""

        try:
            # 🔑 실제 영상 내용만 사용하도록 컨텍스트 제한
            relevant_caption = self._extract_relevant_content(caption, section["content"])

            messages = self.generation_prompt.format_messages(
                viz_type=viz_type,
                topic=topic,
                content=f"섹션: {section['title']}\n내용: {section['content']}\n관련 자막: {relevant_caption}"
            )

            response = self.llm.invoke(messages)

            if response and response.content:
                content_text = response.content.strip()

                # JSON 추출
                if "```json" in content_text:
                    start = content_text.find("```json") + 7
                    end = content_text.find("```", start)
                    if end > start:
                        content_text = content_text[start:end].strip()

                viz_data = json.loads(content_text)

                # 🔑 내용 검증 및 교정
                viz_data = self._correct_content_mismatch(viz_data, topic, section)

                return viz_data

        except Exception as e:
            print(f"⚠️ {viz_type} 생성 실패: {e}")

        # 실패 시 실제 내용 기반 기본 시각화
        return self._create_topic_specific_fallback(viz_type, topic, section)

    def _extract_relevant_content(self, caption: str, section_content: str) -> str:
        """섹션과 관련된 자막 부분만 추출"""

        # 섹션의 핵심 키워드 추출
        section_keywords = re.findall(r'[가-힣]{3,}', section_content)

        # 자막을 문장 단위로 분할
        sentences = re.split(r'[.!?]\s+', caption)

        relevant_sentences = []
        for sentence in sentences:
            # 키워드가 포함된 문장만 선별
            if any(keyword in sentence for keyword in section_keywords[:5]):
                relevant_sentences.append(sentence)

        return ' '.join(relevant_sentences[:3])  # 최대 3문장

    def _correct_content_mismatch(self, viz_data: Dict, topic: str, section: Dict) -> Dict:
        """내용 불일치 교정"""

        # 주제 불일치 감지 및 교정
        data = viz_data.get("data", {})

        if viz_data.get("type") == "mindmap":
            # 중심 주제 교정
            center = data.get("center", "")
            if "중력파" in center and "중력파" not in topic:
                # 실제 주제로 교체
                main_keyword = self._extract_main_keyword(topic)
                data["center"] = main_keyword

            # 브랜치 내용 교정
            branches = data.get("branches", [])
            section_keywords = re.findall(r'[가-힣]{3,}', section["content"])

            for i, branch in enumerate(branches):
                # 섹션 내용과 관련된 키워드로 교체
                if i < len(section_keywords):
                    branch["label"] = section_keywords[i]

                # 하위 항목도 관련 내용으로 교체
                children = branch.get("children", [])
                relevant_terms = self._extract_related_terms(section["content"], branch["label"])
                if relevant_terms:
                    branch["children"] = relevant_terms[:3]

        elif viz_data.get("type") == "flowchart":
            # 플로우차트 노드 내용 교정
            nodes = data.get("nodes", [])
            steps = self._extract_process_steps(section["content"])

            if steps and len(steps) >= 3:
                for i, node in enumerate(nodes):
                    if i < len(steps) and node.get("type") == "process":
                        node["label"] = steps[i]

        viz_data["data"] = data
        return viz_data

    def _extract_main_keyword(self, topic: str) -> str:
        """주제에서 핵심 키워드 추출"""
        words = re.findall(r'[가-힣]{2,}', topic)
        # 가장 긴 단어 또는 의미있는 단어 선택
        meaningful_words = [w for w in words if len(w) >= 3]
        return meaningful_words[0] if meaningful_words else words[0] if words else topic

    def _extract_related_terms(self, content: str, main_term: str) -> List[str]:
        """메인 용어와 관련된 하위 용어들 추출"""
        sentences = content.split('.')
        related_terms = []

        for sentence in sentences:
            if main_term in sentence:
                # 문장에서 의미있는 단어들 추출
                words = re.findall(r'[가-힣]{3,}', sentence)
                for word in words:
                    if word != main_term and word not in related_terms:
                        related_terms.append(word)

        return related_terms[:3] if related_terms else [f"{main_term} 특성", f"{main_term} 활용", f"{main_term} 원리"]

    def _extract_process_steps(self, content: str) -> List[str]:
        """내용에서 실제 과정 단계들 추출"""
        # 번호가 매겨진 단계 찾기
        numbered_steps = re.findall(r'\d+[단계\.]\s*([^.]+)', content)
        if numbered_steps:
            return numbered_steps

        # "먼저", "다음", "마지막" 등의 순서 표현 찾기
        sequence_patterns = [
            r'먼저[,\s]*([^.]+)',
            r'다음[,\s]*([^.]+)',
            r'그\s*다음[,\s]*([^.]+)',
            r'마지막[,\s]*([^.]+)'
        ]

        steps = []
        for pattern in sequence_patterns:
            matches = re.findall(pattern, content)
            steps.extend(matches)

        return steps[:4] if steps else []

    def _validate_content_accuracy(self, viz_data: Dict, topic: str) -> bool:
        """내용 정확성 검증"""

        # 주제 일치성 검증
        data_str = str(viz_data).lower()
        topic_lower = topic.lower()

        # 주제와 완전히 다른 내용이 있는지 확인
        conflicting_topics = ["중력파", "블랙홀", "아인슈타인"]
        topic_keywords = re.findall(r'[가-힣]{2,}', topic_lower)

        for conflict in conflicting_topics:
            if conflict in data_str and not any(keyword in conflict for keyword in topic_keywords):
                print(f"⚠️ 주제 불일치 감지: {conflict} in {topic}")
                return False

        return True

    def _create_topic_specific_fallback(self, viz_type: str, topic: str, section: Dict) -> Dict:
        """주제별 맞춤 기본 시각화"""

        main_keyword = self._extract_main_keyword(topic)
        section_keywords = re.findall(r'[가-힣]{3,}', section["content"])[:3]

        if viz_type == "mindmap":
            return {
                "type": "mindmap",
                "title": f"{topic} 핵심 개념",
                "data": {
                    "center": main_keyword,
                    "branches": [
                        {
                            "label": section_keywords[0] if len(section_keywords) > 0 else "기본 개념",
                            "children": [f"{main_keyword} 정의", f"{main_keyword} 특징", f"{main_keyword} 중요성"]
                        },
                        {
                            "label": section_keywords[1] if len(section_keywords) > 1 else "응용 분야",
                            "children": [f"{main_keyword} 활용", f"{main_keyword} 장점", f"{main_keyword} 효과"]
                        },
                        {
                            "label": section_keywords[2] if len(section_keywords) > 2 else "관련 기술",
                            "children": [f"{main_keyword} 원리", f"{main_keyword} 방법", f"{main_keyword} 기술"]
                        }
                    ]
                }
            }

        elif viz_type == "flowchart":
            steps = self._extract_process_steps(section["content"])
            if not steps:
                steps = [f"{main_keyword} 시작", f"{main_keyword} 진행", f"{main_keyword} 완료"]

            return {
                "type": "flowchart",
                "title": f"{section['title']} 과정",
                "data": {
                    "nodes": [
                        {"id": "1", "label": steps[0] if len(steps) > 0 else "시작", "type": "start"},
                        {"id": "2", "label": steps[1] if len(steps) > 1 else f"{main_keyword} 적용", "type": "process"},
                        {"id": "3", "label": steps[2] if len(steps) > 2 else f"{main_keyword} 검증", "type": "process"},
                        {"id": "4", "label": steps[3] if len(steps) > 3 else "완료", "type": "end"}
                    ],
                    "edges": [
                        {"from": "1", "to": "2"},
                        {"from": "2", "to": "3"},
                        {"from": "3", "to": "4"}
                    ]
                }
            }

        return {
            "type": "paragraph",
            "title": section["title"],
            "content": section["content"]
        }