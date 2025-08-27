import { ColorPalette, lightColors, darkColors, grayColors } from './colors';

export interface Theme {
  name: string;
  colors: ColorPalette;
  spacing: SpacingScale;
  typography: TypographyScale;
}

export interface SpacingScale {
  xs: string;
  sm: string;
  md: string;
  lg: string;
  xl: string;
}

export interface TypographyScale {
  h1: string;
  h2: string;
  h3: string;
  h4: string;
  body: string;
  caption: string;
}

// 间距配置
const spacing: SpacingScale = {
  xs: '0.25rem',
  sm: '0.5rem',
  md: '1rem',
  lg: '1.5rem',
  xl: '2rem',
};

// 字体配置
const typography: TypographyScale = {
  h1: '2.25rem',
  h2: '1.875rem',
  h3: '1.5rem',
  h4: '1.25rem',
  body: '1rem',
  caption: '0.875rem',
};

// 浅色主题（白色基调）
export const lightTheme: Theme = {
  name: 'light',
  colors: lightColors,
  spacing,
  typography,
};

// 深色主题（黑色基调）
export const darkTheme: Theme = {
  name: 'dark',
  colors: darkColors,
  spacing,
  typography,
};

// 灰色主题（灰色基调）
export const grayTheme: Theme = {
  name: 'gray',
  colors: grayColors,
  spacing,
  typography,
};

// 主题映射
export const themes = {
  light: lightTheme,
  dark: darkTheme,
  gray: grayTheme,
};

// 主题类型
export type ThemeName = keyof typeof themes;

// 默认主题
export const defaultTheme = lightTheme;
