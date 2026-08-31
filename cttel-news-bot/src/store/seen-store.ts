import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';

interface SeenStoreData {
  ids: string[];
}

export class SeenStore {
  private readonly filePath: string;
  private ids = new Set<string>();

  private constructor(filePath: string) {
    this.filePath = filePath;
  }

  static async open(dataDir: string): Promise<SeenStore> {
    await mkdir(dataDir, { recursive: true });
    const filePath = path.join(dataDir, 'seen-articles.json');
    const store = new SeenStore(filePath);
    await store.load();
    return store;
  }

  has(id: string): boolean {
    return this.ids.has(id);
  }

  async markSeen(id: string): Promise<void> {
    this.ids.add(id);
    await this.persist();
  }

  async markMany(ids: string[]): Promise<void> {
    for (const id of ids) {
      this.ids.add(id);
    }
    await this.persist();
  }

  private async load(): Promise<void> {
    try {
      const raw = await readFile(this.filePath, 'utf8');
      const parsed = JSON.parse(raw) as SeenStoreData;
      this.ids = new Set(parsed.ids ?? []);
    } catch {
      this.ids = new Set();
    }
  }

  private async persist(): Promise<void> {
    const payload: SeenStoreData = { ids: [...this.ids].slice(-5000) };
    await writeFile(this.filePath, JSON.stringify(payload, null, 2), 'utf8');
  }
}
