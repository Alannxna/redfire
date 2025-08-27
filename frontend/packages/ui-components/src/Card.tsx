import React from 'react';

export interface CardProps {
  children: React.ReactNode;
  title?: string;
  className?: string;
  padding?: 'sm' | 'md' | 'lg';
  shadow?: 'sm' | 'md' | 'lg';
  extra?: React.ReactNode;
  style?: React.CSSProperties;
}

export const Card: React.FC<CardProps> = ({
  children,
  title,
  className = '',
  padding = 'md',
  shadow = 'md',
  extra,
  style,
}) => {
  const paddingClasses = {
    sm: 'p-3',
    md: 'p-4',
    lg: 'p-6',
  };
  
  const shadowClasses = {
    sm: 'shadow-sm',
    md: 'shadow-md',
    lg: 'shadow-lg',
  };
  
  const baseClasses = 'bg-white rounded-lg border border-gray-200';
  const classes = `${baseClasses} ${paddingClasses[padding]} ${shadowClasses[shadow]} ${className}`;
  
  return (
    <div className={classes} style={style}>
      {(title || extra) && (
        <div className="mb-4 flex justify-between items-center">
          {title && <h3 className="text-lg font-semibold text-gray-900">{title}</h3>}
          {extra && <div className="card-extra">{extra}</div>}
        </div>
      )}
      {children}
    </div>
  );
};
