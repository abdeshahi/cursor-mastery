export type LogLevel = 'error' | 'warn' | 'info' | 'debug';

const rank: Record<LogLevel, number> = {
  error: 0,
  warn: 1,
  info: 2,
  debug: 3,
};

export interface Logger {
  error(message: string, meta?: unknown): void;
  warn(message: string, meta?: unknown): void;
  info(message: string, meta?: unknown): void;
  debug(message: string, meta?: unknown): void;
}

export function createLogger(level: LogLevel): Logger {
  const min = rank[level];

  function write(current: LogLevel, message: string, meta?: unknown): void {
    if (rank[current] > min) {
      return;
    }
    const line = {
      ts: new Date().toISOString(),
      level: current,
      message,
      ...(meta === undefined ? {} : { meta }),
    };
    const serialized = JSON.stringify(line);
    if (current === 'error') {
      console.error(serialized);
      return;
    }
    console.log(serialized);
  }

  return {
    error: (message, meta) => write('error', message, meta),
    warn: (message, meta) => write('warn', message, meta),
    info: (message, meta) => write('info', message, meta),
    debug: (message, meta) => write('debug', message, meta),
  };
}
