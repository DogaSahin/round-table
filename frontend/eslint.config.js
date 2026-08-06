import js from '@eslint/js'
import vue from 'eslint-plugin-vue'
import ts from 'typescript-eslint'
import eslintConfigPrettier from 'eslint-config-prettier'

export default ts.config(
  { ignores: ['dist/**', 'node_modules/**', 'coverage/**'] },
  js.configs.recommended,
  ...ts.configs.recommended,
  ...vue.configs['flat/recommended'],
  {
    files: ['**/*.vue'],
    languageOptions: { parserOptions: { parser: ts.parser } },
  },
  {
    // Design-system base/primitive components (Button, Card, Modal, Badge, ...) are
    // intentionally single-word by convention -- they're the atoms, not feature components.
    files: ['src/components/**/*.vue'],
    rules: { 'vue/multi-word-component-names': 'off' },
  },
  eslintConfigPrettier,
)
