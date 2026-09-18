import type { MillStatus, RecipeBatchStatus } from './types';

export const millStatusLabel: Record<MillStatus, string> = {
  grinding: '研磨中',
  idle: '待机',
  wash: '清洗',
};

export const recipeBatchStatusLabel: Record<RecipeBatchStatus, string> = {
  draft: '草稿',
  mixing: '调合中',
  qc_pass: 'QC 合格',
  scrap: '报废',
};
