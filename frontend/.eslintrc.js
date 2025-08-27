/** @type {import('eslint').Linter.Config} */
module.exports = {
  root: true,
  extends: [
    '@redfire/eslint-config/base'
  ],
  parserOptions: {
    project: true,
    tsconfigRootDir: __dirname,
  },
  ignorePatterns: [
    'dist/',
    'build/',
    '.next/',
    'node_modules/',
    '*.config.js',
    '*.config.ts',
  ],
  settings: {
    react: {
      version: 'detect',
    },
  },
};
