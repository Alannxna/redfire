import React, { createContext, useContext, useState, forwardRef, ReactNode } from 'react';

export interface FormProps {
  children: ReactNode;
  onFinish?: (values: Record<string, any>) => void;
  onFinishFailed?: (errorInfo: any) => void;
  layout?: 'horizontal' | 'vertical' | 'inline';
  className?: string;
  style?: React.CSSProperties;
}

export interface FormItemProps {
  label?: string;
  name?: string;
  rules?: Array<{
    required?: boolean;
    message?: string;
    pattern?: RegExp;
    min?: number;
    max?: number;
  }>;
  children: ReactNode;
  className?: string;
  style?: React.CSSProperties;
}

export interface FormInstance {
  validateFields: () => Promise<Record<string, any>>;
  resetFields: () => void;
  setFieldsValue: (values: Record<string, any>) => void;
  getFieldsValue: () => Record<string, any>;
}

interface FormContextType {
  form: FormInstance;
}

const FormContext = createContext<FormContextType | null>(null);

const FormComponent = forwardRef<any, FormProps>(({ 
  children, 
  onFinish, 
  onFinishFailed, 
  layout = 'vertical',
  className,
  style 
}, ref) => {
  const [form] = useState<FormInstance>(() => ({
    validateFields: async () => ({}),
    resetFields: () => {},
    setFieldsValue: (values: Record<string, any>) => {},
    getFieldsValue: () => ({}),
  }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const values = await form.validateFields();
      onFinish?.(values);
    } catch (error) {
      onFinishFailed?.(error);
    }
  };

  return (
    <FormContext.Provider value={{ form }}>
      <form 
        ref={ref}
        onSubmit={handleSubmit}
        className={`form form-${layout} ${className || ''}`}
        style={style}
      >
        {children}
      </form>
    </FormContext.Provider>
  );
});

FormComponent.displayName = 'Form';

export const FormItem: React.FC<FormItemProps> = ({ 
  label, 
  name, 
  rules = [], 
  children, 
  className,
  style 
}) => {
  const [error, setError] = useState<string>('');

  const validateField = (value: any) => {
    for (const rule of rules) {
      if (rule.required && (!value || value.trim() === '')) {
        return rule.message || '此字段是必填的';
      }
      if (rule.pattern && !rule.pattern.test(value)) {
        return rule.message || '格式不正确';
      }
      if (rule.min && value.length < rule.min) {
        return rule.message || `最少需要 ${rule.min} 个字符`;
      }
      if (rule.max && value.length > rule.max) {
        return rule.message || `最多允许 ${rule.max} 个字符`;
      }
    }
    return '';
  };

  const handleChange = (e: any) => {
    const value = e.target?.value || e;
    const errorMsg = validateField(value);
    setError(errorMsg);
  };

  return (
    <div className={`form-item ${className || ''}`} style={style}>
      {label && (
        <label className="form-item-label">
          {rules.some(rule => rule.required) && <span className="required">*</span>}
          {label}
        </label>
      )}
      <div className="form-item-control">
        {React.cloneElement(children as React.ReactElement, {
          onChange: handleChange,
          onBlur: handleChange
        })}
        {error && <div className="form-item-error">{error}</div>}
      </div>
    </div>
  );
};

const SelectComponent: React.FC<{
  children: ReactNode;
  value?: string;
  onChange?: (value: string) => void;
  placeholder?: string;
  className?: string;
  style?: React.CSSProperties;
}> = ({ 
  children, 
  value, 
  onChange, 
  placeholder,
  className,
  style 
}) => {
  return (
    <select
      value={value}
      onChange={(e) => onChange?.(e.target.value)}
      className={`select ${className || ''}`}
      style={style}
    >
      {placeholder && <option value="">{placeholder}</option>}
      {children}
    </select>
  );
};

const SelectOptionComponent: React.FC<{
  children: ReactNode;
  value: string;
}> = ({ children, value }) => {
  return <option value={value}>{children}</option>;
};

// 创建Form组件并添加静态属性
export const Form = Object.assign(FormComponent, {
  Item: FormItem,
  useForm: () => {
    const [form] = useState<FormInstance>(() => ({
      validateFields: async () => ({}),
      resetFields: () => {},
      setFieldsValue: (values: Record<string, any>) => {},
      getFieldsValue: () => ({}),
    }));
    
    return [form];
  }
});

// 创建Select组件并添加静态属性
export const Select = Object.assign(SelectComponent, {
  Option: SelectOptionComponent
});
