function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function translateTextInChunks(
  text: string,
  translateChunk: (chunk: string) => Promise<string>,
  maxChunkSize = 1_800,
): Promise<string> {
  const normalized = text.trim();
  if (normalized.length === 0) {
    return '';
  }

  if (normalized.length <= maxChunkSize) {
    return translateChunk(normalized);
  }

  const paragraphs = normalized.split(/\n{2,}/);
  const chunks: string[] = [];
  let current = '';

  for (const paragraph of paragraphs) {
    const candidate = current.length > 0 ? `${current}\n\n${paragraph}` : paragraph;
    if (candidate.length > maxChunkSize && current.length > 0) {
      chunks.push(current);
      current = paragraph;
      continue;
    }
    current = candidate;
  }

  if (current.length > 0) {
    chunks.push(current);
  }

  const translatedChunks: string[] = [];
  for (const chunk of chunks) {
    translatedChunks.push(await translateChunk(chunk));
    await sleep(800);
  }

  return translatedChunks.join('\n\n').trim();
}
