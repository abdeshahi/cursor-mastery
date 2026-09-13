import winston from 'winston';
import type { Env } from '../config/env.js';

export type Logger = winston.Logger;

export function createLogger(env: Env): Logger {
  return winston.createLogger({
    level: env.LOG_LEVEL,
    format: winston.format.combine(
      winston.format.timestamp(),
      winston.format.errors({ stack: true }),
      winston.format.json(),
    ),
    transports: [new winston.transports.Console()],
  });
}
