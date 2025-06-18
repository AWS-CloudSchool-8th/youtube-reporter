// frontend/src/utils/napkinTheme.js
export const napkinTheme = {
  colors: {
    primary: '#6366f1',
    primaryDark: '#4f46e5',
    secondary: '#ec4899',
    accent: '#10b981',
    background: '#ffffff',
    surface: '#f8fafc',
    text: '#1e293b',
    textSecondary: '#64748b',
    textLight: '#94a3b8',
    border: '#e2e8f0',
    gridLines: '#f1f5f9',
    tooltipBg: 'rgba(30, 41, 59, 0.95)',
    success: '#10b981',
    warning: '#f59e0b',
    error: '#ef4444',

    // Chart specific colors
    chartColors: [
      '#6366f1', '#ec4899', '#10b981', '#f59e0b',
      '#ef4444', '#8b5cf6', '#06b6d4', '#84cc16'
    ]
  },

  gradients: {
    primary: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    secondary: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
    success: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
  },

  fonts: {
    heading: {
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      fontSize: '16px',
      fontWeight: '600',
      lineHeight: '1.5'
    },
    body: {
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      fontSize: '14px',
      fontWeight: '400',
      lineHeight: '1.6'
    },
    caption: {
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      fontSize: '12px',
      fontWeight: '500',
      lineHeight: '1.4'
    }
  },

  // Chart.js 기본 설정
  chartDefaults: {
    responsive: true,
    maintainAspectRatio: false,

    animation: {
      duration: 1000,
      easing: 'easeOutQuart',
    },

    interaction: {
      intersect: false,
      mode: 'index',
    },

    elements: {
      point: {
        radius: 6,
        hoverRadius: 8,
        borderWidth: 2,
        backgroundColor: '#ffffff',
      },
      line: {
        borderWidth: 3,
        tension: 0.2,
        fill: false,
      },
      bar: {
        borderRadius: 8,
        borderSkipped: false,
      },
      arc: {
        borderWidth: 2,
        hoverBorderWidth: 3,
      }
    },

    plugins: {
      legend: {
        display: false, // napkin.ai 스타일
      },
      tooltip: {
        backgroundColor: 'rgba(30, 41, 59, 0.95)',
        titleColor: '#ffffff',
        bodyColor: '#ffffff',
        borderColor: '#e2e8f0',
        borderWidth: 1,
        cornerRadius: 12,
        displayColors: true,
        padding: 12,
        titleFont: {
          size: 14,
          weight: '600',
        },
        bodyFont: {
          size: 13,
          weight: '400',
        },
        titleMarginBottom: 8,
        bodySpacing: 4,
      }
    },

    scales: {
      x: {
        grid: {
          display: false, // 깔끔한 스타일
          drawBorder: false,
        },
        ticks: {
          color: '#64748b',
          font: {
            size: 12,
            weight: '500',
          },
          padding: 8,
        },
        border: {
          display: false,
        }
      },
      y: {
        grid: {
          color: '#f1f5f9',
          borderDash: [2, 2],
          drawBorder: false,
        },
        ticks: {
          color: '#64748b',
          font: {
            size: 12,
            weight: '500',
          },
          padding: 12,
        },
        border: {
          display: false,
        }
      }
    }
  },

  // 컴포넌트별 스타일
  components: {
    card: {
      backgroundColor: '#ffffff',
      borderRadius: '16px',
      boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
      padding: '24px',
      border: '1px solid #f1f5f9',
    },

    button: {
      borderRadius: '12px',
      fontWeight: '600',
      fontSize: '14px',
      padding: '12px 24px',
      border: 'none',
      cursor: 'pointer',
      transition: 'all 0.3s ease',
    },

    input: {
      borderRadius: '12px',
      border: '2px solid #e2e8f0',
      padding: '12px 16px',
      fontSize: '14px',
      transition: 'all 0.3s ease',
      outline: 'none',
    }
  }
};

// Chart.js용 헬퍼 함수들
export const getChartConfig = (type = 'bar') => {
  const baseConfig = { ...napkinTheme.chartDefaults };

  switch (type) {
    case 'bar':
      return {
        ...baseConfig,
        scales: {
          ...baseConfig.scales,
          y: {
            ...baseConfig.scales.y,
            beginAtZero: true,
          }
        }
      };

    case 'line':
      return {
        ...baseConfig,
        elements: {
          ...baseConfig.elements,
          line: {
            ...baseConfig.elements.line,
            fill: {
              target: 'origin',
              above: 'rgba(99, 102, 241, 0.1)',
            }
          }
        }
      };

    case 'pie':
    case 'doughnut':
      return {
        ...baseConfig,
        scales: undefined, // pie 차트는 scales 없음
        plugins: {
          ...baseConfig.plugins,
          legend: {
            display: true,
            position: 'bottom',
            labels: {
              color: napkinTheme.colors.text,
              font: napkinTheme.fonts.body,
              padding: 20,
              usePointStyle: true,
              pointStyle: 'circle',
            }
          }
        }
      };

    default:
      return baseConfig;
  }
};

export const generateChartColors = (count = 1) => {
  const colors = napkinTheme.colors.chartColors;
  const result = [];

  for (let i = 0; i < count; i++) {
    result.push(colors[i % colors.length]);
  }

  return result;
};