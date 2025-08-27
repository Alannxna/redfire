import React from 'react';

export interface ButtonProps {
  children: React.ReactNode;
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  onClick?: () => void;
  className?: string;
  icon?: React.ReactNode;
  type?: 'primary' | 'default' | 'dashed' | 'link' | 'text';
  style?: React.CSSProperties;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  disabled = false,
  onClick,
  className = '',
  icon,
  type,
  style,
}) => {
  const baseClasses = 'px-4 py-2 rounded font-medium transition-colors';
  
  const variantClasses = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700',
    secondary: 'bg-gray-600 text-white hover:bg-gray-700',
    outline: 'border border-gray-300 text-gray-700 hover:bg-gray-50',
    ghost: 'text-gray-700 hover:bg-gray-100',
  };
  
  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2',
    lg: 'px-6 py-3 text-lg',
  };

  // 如果指定了type，使用type；否则使用variant
  const effectiveType = type || variant;
  
  const classes = `${baseClasses} ${variantClasses[effectiveType as keyof typeof variantClasses] || variantClasses.primary} ${sizeClasses[size]} ${className}`;
  
  return (
    <button
      className={classes}
      disabled={disabled}
      onClick={onClick}
      style={style}
    >
      {icon && <span className="button-icon" style={{ marginRight: children ? '8px' : '0' }}>{icon}</span>}
      {children}
    </button>
  );
};
