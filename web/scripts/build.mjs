import { cp, mkdir, rm, readFile, writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const dist = resolve(root, 'dist');
await rm(dist, { recursive: true, force: true });
await mkdir(dist, { recursive: true });
await cp(resolve(root, 'src'), dist, { recursive: true });
await cp(resolve(root, 'engine'), resolve(dist, 'engine'), { recursive: true, filter: path => !/\.test\.mjs$/.test(path) });
const snapshot = JSON.parse(await readFile(resolve(dist, 'engine/snapshot.json'), 'utf8'));
await writeFile(resolve(dist, 'build.json'), JSON.stringify({ builtAt: new Date().toISOString(), revision: snapshot.revision, source: 'https://github.com/hejulian2004/android-interview-notes', static: true }, null, 2));
console.log(`Built ${dist}`);
