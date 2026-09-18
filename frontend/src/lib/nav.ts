import { writable } from 'svelte/store';

export type PageId =
  | 'dashboard'
  | 'workshops'
  | 'mills'
  | 'samples'
  | 'passes'
  | 'batches';

export const page = writable<PageId>('dashboard');

/** 从车间页跳入配方批次时携带的车间筛选（消费一次后清空）。 */
export const batchWorkshopPreset = writable<number | null>(null);

export function go(target: PageId) {
  page.set(target);
}

export function goBatches(workshopId?: number | null) {
  batchWorkshopPreset.set(workshopId ?? null);
  page.set('batches');
}
