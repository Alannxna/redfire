import React from 'react';

export interface InputProps {
  type?: 'text' | 'email' | 'password' | 'number';
  placeholder?: string;
  value?: string | number;
  onChange?: (value: string) => void;
  disabled?: boolean;
  className?: string;
  label?: string;
  error?: string;
  style?: React.CSSProperties;
}

const InputComponent: React.FC<InputProps> = ({
  type = 'text',
  placeholder,
  value,
  onChange,
  disabled = false,
  className = '',
  label,
  error,
  style,
}) => {
  const baseClasses = 'px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500';
  const errorClasses = error ? 'border-red-500' : 'border-gray-300';
  const disabledClasses = disabled ? 'bg-gray-100 cursor-not-allowed' : 'bg-white';
  
  const classes = `${baseClasses} ${errorClasses} ${disabledClasses} ${className}`;
  
  return (
    <div className="space-y-1" style={style}>
      {label && (
        <label className="block text-sm font-medium text-gray-700">
          {label}
        </label>
      )}
      <input
        type={type}
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange?.(e.target.value)}
        disabled={disabled}
        className={classes}
      />
      {error && (
        <p className="text-sm text-red-600">{error}</p>
      )}
    </div>
  );
};

export interface TextAreaProps {
  placeholder?: string;
  value?: string;
  onChange?: (value: string) => void;
  disabled?: boolean;
  className?: string;
  label?: string;
  error?: string;
  rows?: number;
  style?: React.CSSProperties;
}

const TextAreaComponent: React.FC<TextAreaProps> = ({
  placeholder,
  value,
  onChange,
  disabled = false,
  className = '',
  label,
  error,
  rows = 4,
  style,
}) => {
  const baseClasses = 'px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 resize-vertical';
  const errorClasses = error ? 'border-red-500' : 'border-gray-300';
  const disabledClasses = disabled ? 'bg-gray-100 cursor-not-allowed' : 'bg-white';
  
  const classes = `${baseClasses} ${errorClasses} ${disabledClasses} ${className}`;
  
  return (
    <div className="space-y-1" style={style}>
      {label && (
        <label className="block text-sm font-medium text-gray-700">
          {label}
        </label>
      )}
      <textarea
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange?.(e.target.value)}
        disabled={disabled}
        className={classes}
        rows={rows}
      />
      {error && (
        <p className="text-sm text-red-600">{error}</p>
      )}
    </div>
  );
};

// 创建Input组件并添加静态属性
export const Input = Object.assign(InputComponent, {
  TextArea: TextAreaComponent
});
