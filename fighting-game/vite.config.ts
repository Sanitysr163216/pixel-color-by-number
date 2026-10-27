import { defineConfig } from 'vitest/config';

export default defineConfig({
  // Relative paths, so the built game also works from a sub-folder or a single file.
  base: './',
  build: { target: 'es2022' },
  test: { include: ['tests/**/*.test.ts'] },
});
