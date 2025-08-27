/** @type {import('eslint').Linter.Config} */
module.exports = {
  extends: [
    './base.js',
    'plugin:react/recommended',
    'plugin:react-hooks/recommended',
    'plugin:jsx-a11y/recommended',
  ],
  plugins: [
    'react',
    'react-hooks',
    'jsx-a11y',
  ],
  parserOptions: {
    ecmaFeatures: {
      jsx: true,
    },
  },
  settings: {
    react: {
      version: 'detect',
    },
  },
  rules: {
    // React规则
    'react/react-in-jsx-scope': 'off', // React 17+不需要
    'react/prop-types': 'off', // 使用TypeScript
    'react/display-name': 'warn',
    'react/no-unescaped-entities': 'warn',
    'react/jsx-no-target-blank': 'error',
    'react/jsx-key': 'error',
    
    // React Hooks规则
    'react-hooks/rules-of-hooks': 'error',
    'react-hooks/exhaustive-deps': 'warn',
    
    // 无障碍规则
    'jsx-a11y/anchor-is-valid': [
      'error',
      {
        components: ['Link'],
        specialLink: ['hrefLeft', 'hrefRight'],
        aspects: ['invalidHref', 'preferButton'],
      },
    ],
    'jsx-a11y/alt-text': 'error',
    'jsx-a11y/img-redundant-alt': 'error',
    'jsx-a11y/aria-role': 'error',
    
    // JSX格式
    'react/jsx-uses-react': 'off',
    'react/jsx-uses-vars': 'error',
    'react/self-closing-comp': 'error',
    'react/jsx-fragments': ['error', 'syntax'],
  },
};
