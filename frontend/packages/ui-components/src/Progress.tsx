import React from 'react';

export interface ProgressProps {
  percent: number;
  status?: 'success' | 'exception' | 'normal' | 'active';
  strokeWidth?: number;
  showInfo?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

export const Progress: React.FC<ProgressProps> = ({ 
  percent, 
  status = 'normal', 
  strokeWidth = 6, 
  showInfo = true,
  className,
  style 
}) => {
  const getStatusColor = () => {
    switch (status) {
      case 'success':
        return '#52c41a';
      case 'exception':
        return '#ff4d4f';
      case 'active':
        return '#1890ff';
      default:
        return '#1890ff';
    }
  };

  const clampedPercent = Math.min(100, Math.max(0, percent));

  return (
    <div className={`progress ${className || ''}`} style={style}>
      <div className="progress-bar">
        <div 
          className="progress-inner"
          style={{
            width: `${clampedPercent}%`,
            height: strokeWidth,
            backgroundColor: getStatusColor(),
            transition: 'width 0.3s ease'
          }}
        />
      </div>
      {showInfo && (
        <span className="progress-text">
          {clampedPercent.toFixed(0)}%
        </span>
      )}
    </div>
  );
};
