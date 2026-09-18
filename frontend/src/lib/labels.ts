import type { BatchStatus, MillStatus } from './types';

export const millStatusLabel: Record<MillStatus, string> = {
  grinding: '研磨中',
  idle: '待机',
  wash: '清洗',
};

export const batchStatusLabel: Record<BatchStatus, string> = {
  draft: '草稿',
  mixing: '调墨中',
  qc_pass: '质检合格',
  scrap: '报废',
};

// 状态机：draft → mixing；mixing → qc_pass / scrap；qc_pass、scrap 为终态
export const batchNextActions: Partial<
  Record<BatchStatus, { status: BatchStatus; label: string; danger?: boolean }[]>
> = {
  draft: [{ status: 'mixing', label: '开始调墨' }],
  mixing: [
    { status: 'qc_pass', label: '质检合格' },
    { status: 'scrap', label: '报废', danger: true },
  ],
};
