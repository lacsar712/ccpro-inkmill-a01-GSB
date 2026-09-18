<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '../lib/api';
  import { recipeBatchStatusLabel } from '../lib/labels';
  import { batchWorkshopPreset } from '../lib/nav';
  import type { InkRecipeBatch, RecipeBatchStatus, Workshop } from '../lib/types';
  import RecipeBatchDetail from './RecipeBatchDetail.svelte';

  const STATUSES: RecipeBatchStatus[] = ['draft', 'mixing', 'qc_pass', 'scrap'];

  let rows: InkRecipeBatch[] = [];
  let workshops: Workshop[] = [];
  let error = '';
  let editingId: number | null = null;
  let detailId: number | null = null;
  let busy = false;

  let filterWorkshop = '';
  let filterStatus = '';

  let form = {
    workshopId: '',
    batchCode: '',
    pigmentBase: '',
    targetViscosityPaS: '10',
    note: '',
  };

  async function loadWorkshops() {
    workshops = await api<Workshop[]>('/workshops');
  }

  async function load() {
    error = '';
    const params = new URLSearchParams();
    if (filterWorkshop) params.set('workshopId', filterWorkshop);
    if (filterStatus) params.set('status', filterStatus);
    const qs = params.toString();
    try {
      rows = await api<InkRecipeBatch[]>(`/ink-recipe-batches${qs ? `?${qs}` : ''}`);
      if (detailId && !rows.some((r) => r.id === detailId)) detailId = null;
    } catch (e) {
      error = e instanceof Error ? e.message : '加载失败';
    }
  }

  onMount(async () => {
    try {
      await loadWorkshops();
      const preset = $batchWorkshopPreset;
      if (preset != null) {
        filterWorkshop = String(preset);
        form.workshopId = String(preset);
        batchWorkshopPreset.set(null);
      } else if (workshops[0]) {
        form.workshopId = String(workshops[0].id);
      }
      await load();
    } catch (e) {
      error = e instanceof Error ? e.message : '加载失败';
    }
  });

  function workshopName(id: number): string {
    return workshops.find((w) => w.id === id)?.name || `#${id}`;
  }

  $: current = detailId != null ? rows.find((r) => r.id === detailId) ?? null : null;

  function reset() {
    form = {
      workshopId: filterWorkshop || (workshops[0] ? String(workshops[0].id) : ''),
      batchCode: '',
      pigmentBase: '',
      targetViscosityPaS: '10',
      note: '',
    };
    editingId = null;
  }

  function edit(row: InkRecipeBatch) {
    editingId = row.id;
    detailId = row.id;
    form = {
      workshopId: String(row.workshopId),
      batchCode: row.batchCode,
      pigmentBase: row.pigmentBase,
      targetViscosityPaS: String(row.targetViscosityPaS),
      note: row.note || '',
    };
  }

  async function save() {
    error = '';
    const viscosity = Number(form.targetViscosityPaS);
    if (!form.batchCode.trim() || !form.pigmentBase.trim()) {
      error = '批次编号与色浆基料不能为空';
      return;
    }
    if (!(viscosity > 0)) {
      error = '目标粘度(Pa·s)必须大于 0';
      return;
    }
    const payload = {
      workshopId: Number(form.workshopId),
      batchCode: form.batchCode.trim(),
      pigmentBase: form.pigmentBase.trim(),
      targetViscosityPaS: viscosity,
      note: form.note.trim() || null,
    };
    try {
      if (editingId) {
        await api(`/ink-recipe-batches/${editingId}`, {
          method: 'PUT',
          body: JSON.stringify(payload),
        });
      } else {
        const created = await api<InkRecipeBatch>('/ink-recipe-batches', {
          method: 'POST',
          body: JSON.stringify(payload),
        });
        detailId = created.id;
      }
      reset();
      await load();
    } catch (e) {
      error = e instanceof Error ? e.message : '保存失败';
    }
  }

  async function remove(row: InkRecipeBatch) {
    if (!confirm(`确认删除批次 ${row.batchCode}？终态批次不可删除。`)) return;
    error = '';
    try {
      await api(`/ink-recipe-batches/${row.id}`, { method: 'DELETE' });
      if (detailId === row.id) detailId = null;
      await load();
    } catch (e) {
      error = e instanceof Error ? e.message : '删除失败';
    }
  }

  async function transition(row: InkRecipeBatch, to: RecipeBatchStatus) {
    error = '';
    busy = true;
    try {
      await api(`/ink-recipe-batches/${row.id}/transition`, {
        method: 'POST',
        body: JSON.stringify({ to }),
      });
      await load();
    } catch (e) {
      error = e instanceof Error ? e.message : '流转失败';
    } finally {
      busy = false;
    }
  }
</script>

<header class="page-head">
  <h1>色浆配方批次</h1>
  <p>批次挂车间，编号同车间唯一；草稿 → 调合中 → QC 合格 / 报废（后两者为终态）</p>
</header>

{#if error}
  <div class="err">{error}</div>
{/if}

<section class="panel filters">
  <label>车间筛选
    <select bind:value={filterWorkshop} on:change={load}>
      <option value="">全部车间</option>
      {#each workshops as w}
        <option value={String(w.id)}>{w.name}</option>
      {/each}
    </select>
  </label>
  <label>状态筛选
    <select bind:value={filterStatus} on:change={load}>
      <option value="">全部状态</option>
      {#each STATUSES as s}
        <option value={s}>{recipeBatchStatusLabel[s]}</option>
      {/each}
    </select>
  </label>
  <button class="btn-ghost" on:click={() => { filterWorkshop = ''; filterStatus = ''; load(); }}>
    重置筛选
  </button>
</section>

<div class="split">
  <section class="panel list-panel">
    <h2>{editingId ? '编辑批次' : '新增批次'}</h2>
    <div class="fields">
      <div class="field">
        <label>所属车间
          <select bind:value={form.workshopId}>
            {#each workshops as w}
              <option value={String(w.id)}>{w.name}</option>
            {/each}
          </select>
        </label>
      </div>
      <div class="field"><label>批次编号<input bind:value={form.batchCode} placeholder="如 B-2026-004" /></label></div>
      <div class="field"><label>色浆基料<input bind:value={form.pigmentBase} placeholder="如 酞菁蓝 P.B.15:3 色浆" /></label></div>
      <div class="field">
        <label>目标粘度 (Pa·s)
          <input type="number" min="0.0001" step="0.1" bind:value={form.targetViscosityPaS} />
        </label>
      </div>
      <div class="field full"><label>备注<textarea rows="2" bind:value={form.note} /></label></div>
    </div>
    <div class="actions">
      <button class="btn-primary" on:click={save}>{editingId ? '保存' : '创建批次'}</button>
      {#if editingId}
        <button class="btn-ghost" on:click={reset}>取消</button>
      {/if}
    </div>

    <table class="data-table">
      <thead>
        <tr>
          <th>编号</th>
          <th>车间</th>
          <th>色浆基料</th>
          <th>目标粘度(Pa·s)</th>
          <th>状态</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        {#each rows as row}
          <tr class:selected={detailId === row.id}>
            <td><button class="link-btn" on:click={() => (detailId = row.id)}>{row.batchCode}</button></td>
            <td>{workshopName(row.workshopId)}</td>
            <td>{row.pigmentBase}</td>
            <td>{row.targetViscosityPaS}</td>
            <td><span class="badge {row.status}">{recipeBatchStatusLabel[row.status]}</span></td>
            <td class="ops">
              <button class="link-btn" on:click={() => edit(row)}>编辑</button>
              <button class="link-btn danger" on:click={() => remove(row)}>删除</button>
            </td>
          </tr>
        {:else}
          <tr><td colspan="6">暂无批次</td></tr>
        {/each}
      </tbody>
    </table>
  </section>

  {#if current}
    <RecipeBatchDetail
      batch={current}
      workshopName={workshopName(current.workshopId)}
      {busy}
      on:transition={(e) => transition(current, e.detail)}
    />
  {/if}
</div>

<style>
  .filters {
    display: flex;
    gap: 1rem;
    align-items: flex-end;
    flex-wrap: wrap;
  }

  .filters label {
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
    font-size: 0.85rem;
    color: var(--steel);
  }

  .split {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 340px;
    gap: 1rem;
    align-items: start;
  }

  tr.selected {
    background: rgba(192, 57, 43, 0.1);
  }

  @media (max-width: 1000px) {
    .split {
      grid-template-columns: 1fr;
    }
  }
</style>
