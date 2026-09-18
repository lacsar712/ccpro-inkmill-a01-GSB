import { writable } from 'svelte/store';

export type PageId = 'dashboard' | 'workshops' | 'mills' | 'batches' | 'samples' | 'passes';

export const page = writable<PageId>('dashboard');

// 跨页跳转时携带的配方批次筛选预设（例如从车间页跳入）
export const batchFilterPreset = writable<{ workshopId?: number; status?: string } | null>(null);
