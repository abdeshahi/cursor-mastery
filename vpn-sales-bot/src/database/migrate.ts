import 'dotenv/config';
import { readdir, readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { Pool } from 'pg';

import { createPool } from './client.js';

function migrationsDir(): string {
  const here = path.dirname(fileURLToPath(import.meta.url));
  return path.resolve(here, '../../migrations');
}

export async function runMigrations(pool: Pool): Promise<string[]> {
  await pool.query(`
    CREATE TABLE IF NOT EXISTS schema_migrations (
      id TEXT PRIMARY KEY,
      applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
  `);

  const dir = migrationsDir();
  const files = (await readdir(dir))
    .filter((name) => name.endsWith('.sql'))
    .sort((a, b) => a.localeCompare(b));

  const applied: string[] = [];
  for (const file of files) {
    const existing = await pool.query('SELECT 1 FROM schema_migrations WHERE id = $1', [file]);
    if ((existing.rowCount ?? 0) > 0) {
      continue;
    }

    const sql = await readFile(path.join(dir, file), 'utf8');
    const client = await pool.connect();
    try {
      await client.query('BEGIN');
      await client.query(sql);
      await client.query('INSERT INTO schema_migrations (id) VALUES ($1)', [file]);
      await client.query('COMMIT');
      applied.push(file);
    } catch (error) {
      await client.query('ROLLBACK');
      throw error;
    } finally {
      client.release();
    }
  }

  return applied;
}

async function main(): Promise<void> {
  const url = process.env['DATABASE_URL'];
  if (url === undefined || url.length === 0) {
    throw new Error('DATABASE_URL is required');
  }
  const pool = createPool(url);
  try {
    const applied = await runMigrations(pool);
    console.log(applied.length === 0 ? 'No new migrations' : `Applied: ${applied.join(', ')}`);
  } finally {
    await pool.end();
  }
}

const entry = process.argv[1];
if (entry !== undefined && import.meta.url === pathToFileURL(path.resolve(entry)).href) {
  main().catch((error: unknown) => {
    console.error(error);
    process.exit(1);
  });
}
