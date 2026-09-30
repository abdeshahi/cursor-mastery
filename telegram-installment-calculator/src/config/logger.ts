import winston from 'winston';
import type { Environment } from './env.js';

export function createLogger(env: Environment): winston.Logger {
  return winston.createLogger({
    level: env.LOG_LEVEL,
    format: winston.format.combine(winston.format.timestamp(), winston.format.json()),
    transports: [new winston.transports.Console()],
  });
}
