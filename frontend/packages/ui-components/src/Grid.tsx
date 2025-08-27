import React from 'react';

export interface RowProps {
  children: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
  gutter?: number | [number, number];
}

export interface ColProps {
  children: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
  span?: number;
  offset?: number;
  xs?: number;
  sm?: number;
  md?: number;
  lg?: number;
  xl?: number;
}

export const Row: React.FC<RowProps> = ({ children, className, style, gutter = 0 }) => {
  const [horizontalGutter, verticalGutter] = Array.isArray(gutter) ? gutter : [gutter, 0];
  
  return (
    <div 
      className={`row ${className || ''}`} 
      style={{ 
        display: 'flex', 
        flexWrap: 'wrap',
        marginLeft: -horizontalGutter / 2, 
        marginRight: -horizontalGutter / 2,
        marginTop: -verticalGutter / 2,
        marginBottom: -verticalGutter / 2,
        ...style 
      }}
    >
      {React.Children.map(children, (child) => {
        if (React.isValidElement(child)) {
          return React.cloneElement(child, {
            style: { 
              paddingLeft: horizontalGutter / 2, 
              paddingRight: horizontalGutter / 2,
              paddingTop: verticalGutter / 2,
              paddingBottom: verticalGutter / 2,
              ...(child.props as any).style 
            }
          } as any);
        }
        return child;
      })}
    </div>
  );
};

export const Col: React.FC<ColProps> = ({ 
  children, 
  className, 
  style, 
  span = 24, 
  offset = 0,
  xs,
  sm,
  md,
  lg,
  xl
}) => {
  const getResponsiveClasses = () => {
    const classes = [];
    if (xs !== undefined) classes.push(`col-xs-${xs}`);
    if (sm !== undefined) classes.push(`col-sm-${sm}`);
    if (md !== undefined) classes.push(`col-md-${md}`);
    if (lg !== undefined) classes.push(`col-lg-${lg}`);
    if (xl !== undefined) classes.push(`col-xl-${xl}`);
    return classes.join(' ');
  };

  const flexBasis = `${(span / 24) * 100}%`;
  const marginLeft = offset > 0 ? `${(offset / 24) * 100}%` : '0';
  
  return (
    <div 
      className={`col col-${span} ${getResponsiveClasses()} ${className || ''}`} 
      style={{ 
        flex: `0 0 ${flexBasis}`,
        marginLeft,
        ...style 
      }}
    >
      {children}
    </div>
  );
};
