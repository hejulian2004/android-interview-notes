import { cp, mkdir, rm, writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const dist = resolve(root, 'dist');
await rm(dist, { recursive: true, force: true });
await mkdir(dist, { recursive: true });
await cp(resolve(root, 'src'), dist, { recursive: true });
await mkdir(resolve(dist, 'engine'), {recursive:true});
await cp(resolve(root, 'engine/parser.mjs'), resolve(dist, 'engine/parser.mjs'));
await writeFile(resolve(dist, 'build.json'), JSON.stringify({ builtAt: new Date().toISOString(), requiresBackend:true, contentSource:'authenticated-server', staticAssets:true }, null, 2));
console.log(`Built ${dist}`);
