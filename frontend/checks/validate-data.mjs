import { spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const candidates = [
  join(root, '.venv', 'Scripts', 'python.exe'),
  join(root, '.venv', 'bin', 'python'),
  'python',
];
const python = candidates.find(candidate => candidate === 'python' || existsSync(candidate));
const result = spawnSync(python, [
  join(root, 'scripts', 'validate_exports.py'),
  join(root, 'frontend', 'public', 'data'),
], { stdio: 'inherit' });

if (result.error) {
  console.error(result.error.message);
  process.exit(1);
}
process.exit(result.status ?? 1);
