/** @type {import('prettier').Config} */
module.exports = {
  // 基础配置
  printWidth: 80,
  tabWidth: 2,
  useTabs: false,
  semi: true,
  singleQuote: true,
  quoteProps: 'as-needed',
  
  // JSX配置
  jsxSingleQuote: false,
  
  // 尾随逗号
  trailingComma: 'es5',
  
  // 括号配置
  bracketSpacing: true,
  bracketSameLine: false,
  arrowParens: 'avoid',
  
  // 换行符
  endOfLine: 'lf',
  
  // 嵌入语言格式化
  embeddedLanguageFormatting: 'auto',
  
  // 覆盖特定文件
  overrides: [
    {
      files: '*.md',
      options: {
        printWidth: 100,
        proseWrap: 'always',
      },
    },
    {
      files: '*.json',
      options: {
        printWidth: 100,
      },
    },
    {
      files: '*.yml',
      options: {
        singleQuote: false,
      },
    },
  ],
};