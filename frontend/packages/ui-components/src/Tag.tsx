import React from 'react';

export interface TagProps {
  children: React.ReactNode;
  color?: string;
  closable?: boolean;
  onClose?: () => void;
  className?: string;
  style?: React.CSSProperties;
}

export const Tag: React.FC<TagProps> = ({ 
  children, 
  color = 'default', 
  closable = false, 
  onClose,
  className,
  style 
}) => {
  const getColorStyle = () => {
    switch (color) {
      case 'success':
        return { backgroundColor: '#f6ffed', borderColor: '#b7eb8f', color: '#52c41a' };
      case 'warning':
        return { backgroundColor: '#fffbe6', borderColor: '#ffe58f', color: '#faad14' };
      case 'error':
        return { backgroundColor: '#fff2f0', borderColor: '#ffccc7', color: '#ff4d4f' };
      case 'processing':
        return { backgroundColor: '#e6f7ff', borderColor: '#91d5ff', color: '#1890ff' };
      default:
        return { backgroundColor: '#fafafa', borderColor: '#d9d9d9', color: 'rgba(0, 0, 0, 0.85)' };
    }
  };

  return (
    <span 
      className={`tag tag-${color} ${className || ''}`} 
      style={{ 
        display: 'inline-block',
        padding: '0 7px',
        fontSize: '12px',
        lineHeight: '20px',
        whiteSpace: 'nowrap',
        background: '#fff',
        border: '1px solid #d9d9d9',
        borderRadius: '2px',
        cursor: 'default',
        ...getColorStyle(),
        ...style 
      }}
    >
      {children}
      {closable && (
        <span 
          className="tag-close-icon"
          onClick={onClose}
          style={{
            marginLeft: '6px',
            cursor: 'pointer',
            fontSize: '10px',
            lineHeight: '22px'
          }}
        >
          ×
        </span>
      )}
    </span>
  );
};
