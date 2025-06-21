import React, { useState, useEffect } from 'react';
import AdvancedVisualization from './AdvancedVisualization';
import './ResultViewer.css';

const ResultViewer = ({ result }) => {
  const [activeSection, setActiveSection] = useState('');
  const [summaryLevel, setSummaryLevel] = useState('detailed');

  // 스크롤 감지
  useEffect(() => {
    if (!result) return;
    
    const handleScroll = () => {
      const sections = document.querySelectorAll('[id^="section-"]');
      let currentSection = '';
      
      sections.forEach(section => {
        const rect = section.getBoundingClientRect();
        if (rect.top <= 100 && rect.bottom >= 100) {
          currentSection = section.id;
        }
      });
      
      if (currentSection) {
        setActiveSection(currentSection);
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [result]);

  if (!result) return null;

  // 스크롤 네비게이션
  const scrollToSection = (sectionId) => {
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
      setActiveSection(sectionId);
    }
  };

  // PDF 내보내기
  const exportToPDF = () => {
    window.print();
  };

  // 키워드 하이라이팅
  const highlightKeywords = (text) => {
    if (!text || typeof text !== 'string') return text;
    
    const keywords = ['중요', '핵심', '주요', '필수', '권장', '추천'];
    let highlightedText = text;
    
    keywords.forEach(keyword => {
      const regex = new RegExp(`(${keyword})`, 'gi');
      highlightedText = highlightedText.replace(regex, '<mark class="keyword-highlight">$1</mark>');
    });
    
    return <span dangerouslySetInnerHTML={{ __html: highlightedText }} />;
  };

  // 요약 레벨에 따른 내용 필터링
  const getContentByLevel = (content, level) => {
    if (!content) return content;
    
    if (level === 'simple') {
      const sentences = content.split('.');
      return sentences.slice(0, 2).join('.') + (sentences.length > 2 ? '...' : '');
    } else if (level === 'expert') {
      return content + (content.includes('전문가') ? '' : '\n\n[전문가 관점] 이 내용은 실무 적용 시 다양한 변수를 고려해야 합니다.');
    }
    return content;
  };

  // 섹션 렌더러
  const renderSection = (section, index) => {
    const { id, type, title, content, data, subsections } = section;
    const sectionId = id || `section-${index}`;

    const visualizationTypes = [
      'bar_chart', 'line_chart', 'pie_chart', 'heatmap', 
      'network', 'timeline', 'process_flow', 'comparison_table'
    ];

    if (visualizationTypes.includes(type)) {
      return (
        <div key={index} id={sectionId} className="visualization-section">
          <h2 className="section-title">{title}</h2>
          <div className="visualization-wrapper">
            <AdvancedVisualization type={type} data={data} title={title} />
          </div>
        </div>
      );
    }

    return (
      <div key={index} id={sectionId} className="report-section">
        <h2 className="section-title">{title}</h2>
        <div className="section-content">
          {highlightKeywords(getContentByLevel(content, summaryLevel))}
        </div>
        {subsections && summaryLevel !== 'simple' && (
          <div className="subsections">
            {subsections.slice(0, summaryLevel === 'expert' ? subsections.length : 3).map((subsection, subIndex) => (
              <div key={subIndex} className="subsection">
                <h3 className="subsection-title">{subsection.title}</h3>
                <div className="subsection-content">
                  {highlightKeywords(getContentByLevel(subsection.content, summaryLevel))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };



  return (
    <div className="result-viewer">
      {/* 헤더 */}
      <div className="result-header">
        <h1 className="result-title">{result.title}</h1>
        <div className="result-controls">
          <div className="summary-level-selector">
            <label>요약 레벨:</label>
            <select value={summaryLevel} onChange={(e) => setSummaryLevel(e.target.value)}>
              <option value="simple">간단</option>
              <option value="detailed">상세</option>
              <option value="expert">전문가</option>
            </select>
          </div>
          <button onClick={exportToPDF} className="export-btn">
            📄 PDF 내보내기
          </button>
        </div>
      </div>

      <div className="result-body">
        {/* 목차 네비게이션 */}
        {result.tableOfContents && (
          <div className="table-of-contents">
            <h3>📋 목차</h3>
            <nav className="toc-nav">
              {result.tableOfContents.map((item, index) => (
                <button
                  key={index}
                  className={`toc-item ${activeSection === item.id ? 'active' : ''}`}
                  onClick={() => scrollToSection(item.id)}
                >
                  {item.title}
                </button>
              ))}
            </nav>
          </div>
        )}

        {/* 메인 콘텐츠 */}
        <div className="main-content">
          {result.sections && result.sections.length > 0 ? (
            result.sections
              .filter((section, index) => {
                if (summaryLevel === 'simple' && section.type !== 'section' && section.type !== 'heading') {
                  return index < 1;
                }
                return true;
              })
              .map((section, index) => renderSection(section, index))
          ) : (
            <div className="no-content">
              <p>표시할 내용이 없습니다.</p>
            </div>
          )}
        </div>
      </div>

      {/* 플로팅 네비게이션 */}
      <div className="floating-nav">
        <button 
          className="nav-btn"
          onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
          title="맨 위로"
        >
          ⬆️
        </button>
        <button 
          className="nav-btn"
          onClick={() => window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' })}
          title="맨 아래로"
        >
          ⬇️
        </button>
      </div>
    </div>
  );
};

export default ResultViewer;