import React from 'react';

export interface LayoutProps {
  children: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
}

export const Layout: React.FC<LayoutProps> = ({ children, className, style }) => {
  return (
    <div className={`layout ${className || ''}`} style={style}>
      {children}
    </div>
  );
};

export const Header: React.FC<LayoutProps> = ({ children, className, style }) => {
  return (
    <header className={`layout-header ${className || ''}`} style={style}>
      {children}
    </header>
  );
};

export const Content: React.FC<LayoutProps> = ({ children, className, style }) => {
  return (
    <main className={`layout-content ${className || ''}`} style={style}>
      {children}
    </main>
  );
};

export const Sider: React.FC<LayoutProps> = ({ children, className, style }) => {
  return (
    <aside className={`layout-sider ${className || ''}`} style={style}>
      {children}
    </aside>
  );
};

export const Footer: React.FC<LayoutProps> = ({ children, className, style }) => {
  return (
    <footer className={`layout-footer ${className || ''}`} style={style}>
      {children}
    </footer>
  );
};
