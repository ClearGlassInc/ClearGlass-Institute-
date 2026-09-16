import { mkdirSync, copyFileSync, writeFileSync, existsSync } from 'node:fs';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const pkg = require('../package.json');

mkdirSync('dist', { recursive: true });

const manifest = {
  name: pkg.name,
  version: pkg.version,
  description: pkg.description,
  homepage: pkg.homepage,
  repository: pkg.repository,
  main: pkg.main,
  bin: pkg.bin,
  builtAt: new Date().toISOString()
};

writeFileSync('dist/opal-koboi.manifest.json', `${JSON.stringify(manifest, null, 2)}\n`, 'utf8');
writeFileSync('dist/README.txt', 'Opal-Koboi build complete. Use npm start, npm run plan, or npm run run.\n', 'utf8');

if (existsSync('README.md')) {
  copyFileSync('README.md', 'dist/README.md');
}

console.log(`Built ${pkg.name}@${pkg.version} into dist/.`);
