// frontend/src/components/ResultViewer.jsx
import React, { useState, useEffect } from 'react';
import SmartVisualization from './SmartVisualization';
import './ResultViewer.css';

const ResultViewer = ({ result }) => {
  const [activeSection, setActiveSection] = useState('');
  const [expandedSections, setExpandedSections] = useState(new Set());

  useEffect(() => {
    // 스크롤 감지하여 활성 섹션 업데이트
    const handleScroll = () => {
      const sections = document.querySelectorAll('.report-section');
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
  }, []);

  if (!result) return null;

  const toggleSection = (sectionId) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(sectionId)) {
      newExpanded.delete(sectionId);
    } else {
      newExpanded.add(sectionId);
    }
    setExpandedSections(newExpanded);
  };

  const scrollToSection = (sectionId) => {
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  const exportToPDF = () => {
    window.print();
  };

  const copyToClipboard = () => {
    const textContent = result.sections
      .filter(s => s.type === 'text')
      .map(s => `${s.title}\n\n${s.content}`)
      .join('\n\n---\n\n');

    navigator.clipboard.writeText(textContent).then(() => {
      alert('텍스트가 클립보드에 복사되었습니다.');
    });
  };

  const renderSection = (section, index) => {
    const sectionId = section.id || `section-${index}`;
    const isExpanded = expandedSections.has(sectionId) || section.level === 1;

    if (section.type === 'text') {
      return (
        <div key={sectionId} id={sectionId} className="report-section text-section">
          <div
            className={`section-header level-${section.level || 2}`}
            onClick={() => toggleSection(sectionId)}
          >
            <h3>
              <span className="toggle-icon">{isExpanded ? '▼' : '▶'}</span>
              {section.title}
            </h3>
            {section.keywords && section.keywords.length > 0 && (
              <div className="keywords">
                {section.keywords.map((keyword, i) => (
                  <span key={i} className="keyword">{keyword}</span>
                ))}
              </div>
            )}
          </div>
          {isExpanded && (
            <div className="section-content">
              <p>{section.content}</p>
            </div>
          )}
        </div>
      );
    }

    if (section.type === 'visualization') {
      return (
        <div key={sectionId} id={sectionId} className="report-section visualization-section">
          <SmartVisualization section={section} />
        </div>
      );
    }

    return null;
  };

  const textSections = result.sections?.filter(s => s.type === 'text') || [];
  const visualSections = result.sections?.filter(s => s.type === 'visualization') || [];

  return (
    <div className="result-viewer">
      {/* 헤더 */}
      <div className="result-header">
        <div className="header-content">
          <h1 className="result-title">{result.title}</h1>
          {result.summary && (
            <p className="result-summary">{result.summary}</p>
          )}
        </div>

        <div className="result-actions">
          <button onClick={exportToPDF} className="action-btn export-btn">
            📄 PDF 내보내기
          </button>
          <button onClick={copyToClipboard} className="action-btn copy-btn">
            📋 텍스트 복사
          </button>
        </div>
      </div>

      {/* 통계 */}
      {result.statistics && (
        <div className="result-statistics">
          <div className="stat-item">
            <span className="stat-number">{result.statistics.total_sections || 0}</span>
            <span className="stat-label">전체 섹션</span>
          </div>
          <div className="stat-item">
            <span className="stat-number">{result.statistics.text_sections || 0}</span>
            <span className="stat-label">텍스트 섹션</span>
          </div>
          <div className="stat-item">
            <span className="stat-number">{result.statistics.visualizations || 0}</span>
            <span className="stat-label">시각화</span>
          </div>
          {result.success && (
            <div className="stat-item success">
              <span className="stat-icon">✅</span>
              <span className="stat-label">분석 성공</span>
            </div>
          )}
        </div>
      )}

      <div className="result-body">
        {/* 목차 (선택적) */}
        {textSections.length > 3 && (
          <aside className="table-of-contents">
            <h3>📑 목차</h3>
            <nav>
              {textSections.map((section, index) => (
                <button
                  key={section.id || index}
                  className={`toc-item ${activeSection === (section.id || `section-${index}`) ? 'active' : ''}`}
                  onClick={() => scrollToSection(section.id || `section-${index}`)}
                >
                  {section.title}
                </button>
              ))}
            </nav>
          </aside>
        )}

        {/* 메인 콘텐츠 */}
        <div className="main-content">
          {result.sections && result.sections.length > 0 ? (
            result.sections.map((section, index) => renderSection(section, index))
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
        {visualSections.length > 0 && (
          <button
            className="nav-btn highlight"
            onClick={() => {
              const firstViz = document.querySelector('.visualization-section');
              if (firstViz) firstViz.scrollIntoView({ behavior: 'smooth' });
            }}
            title="첫 시각화로"
          >
            📊
          </button>
        )}
      </div>
    </div>
  );
};

export default ResultViewer;