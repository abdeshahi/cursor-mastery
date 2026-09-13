import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

const plans = [
  {
    months: 6,
    creditPercent: '92',
    servicePercent: '8',
    monthlyInstallmentFactor: '0.17802',
    minimumLoan: 0n,
    maximumLoan: null,
    sortOrder: 1,
  },
  {
    months: 12,
    creditPercent: '87',
    servicePercent: '13',
    monthlyInstallmentFactor: '0.094076',
    minimumLoan: 500_000_000n,
    maximumLoan: null,
    sortOrder: 2,
  },
  {
    months: 18,
    creditPercent: '83',
    servicePercent: '17',
    monthlyInstallmentFactor: '0.066214',
    minimumLoan: 1_000_000_000n,
    maximumLoan: 3_000_000_000n,
    sortOrder: 3,
  },
  {
    months: 24,
    creditPercent: '80',
    servicePercent: '20',
    monthlyInstallmentFactor: '0.052373',
    minimumLoan: 1_000_000_000n,
    maximumLoan: 3_000_000_000n,
    sortOrder: 4,
  },
  {
    months: 36,
    creditPercent: '74',
    servicePercent: '26',
    monthlyInstallmentFactor: '0.0387095',
    minimumLoan: 1_000_000_000n,
    maximumLoan: 3_250_000_000n,
    sortOrder: 5,
  },
] as const;

async function main() {
  for (const plan of plans) {
    await prisma.plan.upsert({
      where: { months: plan.months },
      create: plan,
      update: {
        creditPercent: plan.creditPercent,
        servicePercent: plan.servicePercent,
        monthlyInstallmentFactor: plan.monthlyInstallmentFactor,
        minimumLoan: plan.minimumLoan,
        maximumLoan: plan.maximumLoan,
        sortOrder: plan.sortOrder,
      },
    });
  }

  await prisma.setting.upsert({
    where: { key: 'store_name' },
    create: { key: 'store_name', value: 'CTTEL' },
    update: { value: 'CTTEL' },
  });
}

main()
  .then(async () => {
    await prisma.$disconnect();
  })
  .catch(async (error: unknown) => {
    console.error(error);
    await prisma.$disconnect();
    process.exit(1);
  });
