<script lang="ts">
  import { recipeBatchStatusLabel } from '../lib/labels';
  import type { InkRecipeBatch, RecipeBatchStatus } from '../lib/types';

  export let batch: InkRecipeBatch;
  export let workshopName: string;
  export let busy = false;

  import { createEventDispatcher } from 'svelte';
  const dispatch = createEventDispatcher<{ transition: RecipeBatchStatus }>();
</script>

<section class="panel detail-panel">
  <h2>批次详情 · {batch.batchCode}</h2>
  <dl class="kv">
    <div><dt>所属车间</dt><dd>{workshopName}</dd></div>
    <div><dt>色浆基料</dt><dd>{batch.pigmentBase}</dd></div>
    <div><dt>目标粘度</dt><dd>{batch.targetViscosityPaS} Pa·s</dd></div>
    <div>
      <dt>当前状态</dt>
      <dd><span class="badge {batch.status}">{recipeBatchStatusLabel[batch.status]}</span></dd>
    </div>
    <div><dt>备注</dt><dd>{batch.note || '—'}</dd></div>
    <div><dt>创建时间</dt><dd>{batch.createdAt}</dd></div>
    <div><dt>更新时间</dt><dd>{batch.updatedAt}</dd></div>
  </dl>

  <h3>状态流转</h3>
  {#if batch.status === 'draft'}
    <button class="btn-primary flow" disabled={busy} on:click={() => dispatch('transition', 'mixing')}>
      开始调合（→ 调合中）
    </button>
    <p class="muted">草稿批次投料后进入调合。</p>
  {:else if batch.status === 'mixing'}
    <div class="flow-row">
      <button class="btn-primary flow" disabled={busy} on:click={() => dispatch('transition', 'qc_pass')}>
        QC 合格（终态）
      </button>
      <button class="btn-danger flow" disabled={busy} on:click={() => dispatch('transition', 'scrap')}>
        报废（终态）
      </button>
    </div>
    <p class="muted">调合完成后按质检结果流转，终态不可逆。</p>
  {:else}
    <p class="muted">该批次已处于终态「{recipeBatchStatusLabel[batch.status]}」，不可再流转。</p>
  {/if}
</section>

<style>
  .kv {
    display: flex;
    flex-direction: column;
    gap: 0.55rem;
    margin: 0 0 1.2rem;
  }

  .kv > div {
    display: grid;
    grid-template-columns: 88px 1fr;
    gap: 0.5rem;
    font-size: 0.9rem;
  }

  .kv dt {
    color: var(--steel);
  }

  .kv dd {
    margin: 0;
  }

  .detail-panel h3 {
    margin: 0.4rem 0 0.7rem;
    font-size: 0.95rem;
  }

  .flow {
    width: 100%;
    margin-bottom: 0.5rem;
  }

  .flow-row {
    display: flex;
    gap: 0.6rem;
  }

  .flow-row .flow {
    flex: 1;
  }

  .btn-danger {
    background: #5c1410;
    border: 1px solid var(--vermillion-700);
    color: #ffd9d4;
    padding: 0.6rem 0.9rem;
    cursor: pointer;
  }

  .btn-danger:hover {
    background: var(--vermillion-900);
  }
</style>
