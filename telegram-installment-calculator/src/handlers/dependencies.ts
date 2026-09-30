import type { AdminService } from '../services/admin-service.js';
import type { CalculatorService } from '../services/calculator-service.js';
import type { ExportService } from '../services/export-service.js';
import type {
  PrismaSettingRepository,
  UserRepository,
} from '../database/repositories.js';

export interface BotDependencies {
  adminId: string;
  admin: AdminService;
  calculator: CalculatorService;
  users: UserRepository;
  exports: ExportService;
  settings: PrismaSettingRepository;
}

export type HandlerDependencies = BotDependencies;
