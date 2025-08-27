export interface ColorPalette {
  primary: string;
  secondary: string;
  success: string;
  warning: string;
  error: string;
  background: string;
  surface: string;
  text: string;
  border: string;
  hover: string;
  active: string;
  muted: string;
  cardBg: string;
  headerBg: string;
  sidebarBg: string;
}

// 黑白灰基础色板
export const monochromeColors = {
  black: '#000000',
  darkGray: '#2D2D2D',
  mediumGray: '#6B7280',
  lightGray: '#9CA3AF',
  paleGray: '#E5E7EB',
  offWhite: '#F9FAFB',
  white: '#FFFFFF',
};

// 默认色板（保持兼容性）
export const colors: ColorPalette = {
  primary: '#2D2D2D',
  secondary: '#6B7280',
  success: '#2D2D2D',
  warning: '#6B7280',
  error: '#2D2D2D',
  background: '#FFFFFF',
  surface: '#F9FAFB',
  text: '#2D2D2D',
  border: '#E5E7EB',
  hover: '#F9FAFB',
  active: '#E5E7EB',
  muted: '#9CA3AF',
  cardBg: '#FFFFFF',
  headerBg: '#FFFFFF',
  sidebarBg: '#2D2D2D',
};

// 浅色主题
export const lightColors: ColorPalette = {
  primary: '#2D2D2D',
  secondary: '#6B7280',
  success: '#2D2D2D',
  warning: '#6B7280',
  error: '#2D2D2D',
  background: '#FFFFFF',
  surface: '#F9FAFB',
  text: '#2D2D2D',
  border: '#E5E7EB',
  hover: '#F9FAFB',
  active: '#E5E7EB',
  muted: '#9CA3AF',
  cardBg: '#FFFFFF',
  headerBg: '#FFFFFF',
  sidebarBg: '#2D2D2D',
};

// 深色主题
export const darkColors: ColorPalette = {
  primary: '#E5E7EB',
  secondary: '#9CA3AF',
  success: '#E5E7EB',
  warning: '#9CA3AF',
  error: '#E5E7EB',
  background: '#000000',
  surface: '#2D2D2D',
  text: '#F9FAFB',
  border: '#6B7280',
  hover: '#2D2D2D',
  active: '#6B7280',
  muted: '#6B7280',
  cardBg: '#2D2D2D',
  headerBg: '#000000',
  sidebarBg: '#000000',
};

// 灰色主题
export const grayColors: ColorPalette = {
  primary: '#2D2D2D',
  secondary: '#6B7280',
  success: '#2D2D2D',
  warning: '#6B7280',
  error: '#2D2D2D',
  background: '#F9FAFB',
  surface: '#E5E7EB',
  text: '#2D2D2D',
  border: '#9CA3AF',
  hover: '#E5E7EB',
  active: '#9CA3AF',
  muted: '#6B7280',
  cardBg: '#E5E7EB',
  headerBg: '#F9FAFB',
  sidebarBg: '#6B7280',
};
