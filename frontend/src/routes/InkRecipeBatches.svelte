<script lang="ts">
  import { onMount } from 'svelte';
  import { get } from 'svelte/store';
  import { api } from '../lib/api';
  import { batchStatusLabel, batchNextActions } from '../lib/labels';
  import { batchFilterPreset } from '../lib/nav';
  import type { BatchStatus, InkRecipeBatch, Workshop } from '../lib/types';

  let rows: InkRecipeBatch[] = [];
  let workshops: Workshop[] = [];
  let error = '';
  let editingId: number | null = null;
  let selectedId: number | null = null;
  let transitionNote = '';

  let filterWorkshop = '';
  let filterStatus = '';

  let form = {
    workshopId: '',
    batchCode: '',
    pigmentBase: '',
    targetViscosityPaS: '10',
    note: '',
  };

  async function load() {
    error = '';
    try {
      const params = new URLSearchParams();
      if (filterWorkshop) params.set('workshopId', filterWorkshop);
      if (filterStatus) params.set('status', filterStatus);
      const query = params.toString() ? `?${params.toString()}` : '';
      rows = await api<InkRecipeBatch[]>(`/ink-recipe-batches${query}`);
      if (selectedId && !rows.some((r) => r.id === selectedId)) {
        selectedId = null;
      }
    } catch (e) {
      error = e instanceof Error ? e.message : '加载失败';
    }
  }

  onMount(async () => {
    try {
      workshops = await api<Workshop[]>('/workshops');
    } catch (e) {
      error = e instanceof Error ? e.message : '车间加载失败';
    }

    // 从车间页跳入时携带 workshopId（可选 status）
    const preset = get(batchFilterPreset);
    if (preset) {
      filterWorkshop = preset.workshopId ? String(preset.workshopId) : '';
      filterStatus = preset.status || '';
      batchFilterPreset.set(null);
    }
    if (!form.workshopId) {
      form.workshopId = filterWorkshop || (workshops[0] ? String(workshops[0].id) : '');
    }
    await load();
  });

  function workshopName(id: number): string {
    return workshops.find((w) => w.id === id)?.name || `#${id}`;
  }

  $: selected = rows.find((r) => r.id === selectedId) || null;

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
    selectedId = null;
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
    const payload = {
      workshopId: Number(form.workshopId),
      batchCode: form.batchCode,
      pigmentBase: form.pigmentBase,
      targetViscosityPaS: Number(form.targetViscosityPaS),
      note: form.note || null,
    };
    try {
      if (editingId) {
        await api(`/ink-recipe-batches/${editingId}`, {
          method: 'PUT',
          body: JSON.stringify(payload),
        });
      } else {
        await api('/ink-recipe-batches', {
          method: 'POST',
          body: JSON.stringify(payload),
        });
      }
      reset();
      await load();
    } catch (e) {
      error = e instanceof Error ? e.message : '保存失败';
    }
  }

  async function remove(row: InkRecipeBatch) {
    if (!confirm(`确认删除配方批次 ${row.batchCode}？`)) return;
    try {
      await api(`/ink-recipe-batches/${row.id}`, { method: 'DELETE' });
      if (selectedId === row.id) selectedId = null;
      await load();
    } catch (e) {
      error = e instanceof Error ? e.message : '删除失败';
    }
  }

  function openDetail(row: InkRecipeBatch) {
    selectedId = row.id;
    editingId = null;
    transitionNote = row.note || '';
  }

  async function transition(row: InkRecipeBatch, target: BatchStatus) {
    if (target === 'scrap' && !confirm(`确认将批次 ${row.batchCode} 整批报废？报废后不可恢复。`)) {
      return;
    }
    error = '';
    try {
      await api(`/ink-recipe-batches/${row.id}/transition`, {
        method: 'POST',
        body: JSON.stringify({ status: target, note: transitionNote || null }),
      });
      await load();
    } catch (e) {
      error = e instanceof Error ? e.message : '流转失败';
    }
  }
</script>

<header class="page-head">
  <h1>色浆配方批次</h1>
  <p>批次编号在同一车间内唯一；流转：草稿 → 调墨中 → 质检合格 / 报废，合格与报废为终态</p>
</header>

{#if error}
  <div class="err">{error}</div>
{/if}

<section class="panel">
  <h2>筛选</h2>
  <div class="filters">
    <label>车间
      <select bind:value={filterWorkshop} on:change={load}>
        <option value="">全部车间</option>
        {#each workshops as w}
          <option value={String(w.id)}>{w.name}</option>
        {/each}
      </select>
    </label>
    <label>状态
      <select bind:value={filterStatus} on:change={load}>
        <option value="">全部状态</option>
        <option value="draft">草稿</option>
        <option value="mixing">调墨中</option>
        <option value="qc_pass">质检合格</option>
        <option value="scrap">报废</option>
      </select>
    </label>
    <button class="btn-ghost" on:click={load}>刷新</button>
    {#if filterWorkshop || filterStatus}
      <button
        class="btn-ghost"
        on:click={() => {
          filterWorkshop = '';
          filterStatus = '';
          load();
        }}
      >
        清除筛选
      </button>
    {/if}
  </div>
</section>

<section class="panel">
  <h2>{editingId ? '编辑配方批次（状态仅可通过详情流转）' : '新建配方批次'}</h2>
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
    <div class="field"><label>批次编号<input bind:value={form.batchCode} placeholder="如 PB-2026-010" /></label></div>
    <div class="field"><label>色浆基料<input bind:value={form.pigmentBase} /></label></div>
    <div class="field">
      <label>目标粘度 (Pa·s)<input type="number" min="0.0001" step="0.0001" bind:value={form.targetViscosityPaS} /></label>
    </div>
    <div class="field full"><label>备注<textarea rows="2" bind:value={form.note} /></label></div>
  </div>
  <div class="actions">
    <button class="btn-primary" on:click={save}>{editingId ? '保存' : '创建（草稿）'}</button>
    {#if editingId}
      <button class="btn-ghost" on:click={reset}>取消</button>
    {/if}
  </div>
</section>

{#if selected}
  <section class="panel detail">
    <h2>批次详情 · {selected.batchCode}</h2>
    <div class="detail-grid">
      <div><span class="muted">ID</span><b>{selected.id}</b></div>
      <div><span class="muted">所属车间</span><b>{workshopName(selected.workshopId)}</b></div>
      <div><span class="muted">批次编号</span><b>{selected.batchCode}</b></div>
      <div><span class="muted">色浆基料</span><b>{selected.pigmentBase}</b></div>
      <div><span class="muted">目标粘度</span><b>{selected.targetViscosityPaS} Pa·s</b></div>
      <div>
        <span class="muted">当前状态</span>
        <b><span class="badge {selected.status}">{batchStatusLabel[selected.status]}</span></b>
      </div>
      <div><span class="muted">创建时间</span><b>{selected.createdAt}</b></div>
      <div><span class="muted">更新时间</span><b>{selected.updatedAt}</b></div>
    </div>
    <div class="field note-edit">
      <label>流转备注（可选，随本次流转保存）
        <textarea rows="2" bind:value={transitionNote} />
      </label>
    </div>
    <div class="actions">
      {#each batchNextActions[selected.status] || [] as act}
        <button
          class={act.danger ? 'btn-danger' : 'btn-primary'}
          on:click={() => transition(selected, act.status)}
        >
          {act.label}
        </button>
      {:else}
        <span class="muted">该状态为终态，不可继续流转。</span>
      {/each}
      <button class="btn-ghost" on:click={() => (selectedId = null)}>关闭详情</button>
    </div>
  </section>
{/if}

<section class="panel">
  <table class="data-table">
    <thead>
      <tr>
        <th>ID</th>
        <th>车间</th>
        <th>批次编号</th>
        <th>色浆基料</th>
        <th>目标粘度(Pa·s)</th>
        <th>状态</th>
        <th>备注</th>
        <th></th>
      </tr>
    </thead>
    <tbody>
      {#each rows as row}
        <tr class:row-active={selectedId === row.id}>
          <td>{row.id}</td>
          <td>{workshopName(row.workshopId)}</td>
          <td>{row.batchCode}</td>
          <td>{row.pigmentBase}</td>
          <td>{row.targetViscosityPaS}</td>
          <td><span class="badge {row.status}">{batchStatusLabel[row.status]}</span></td>
          <td>{row.note || '—'}</td>
          <td class="ops">
            <button class="link-btn" on:click={() => openDetail(row)}>详情/流转</button>
            <button class="link-btn" on:click={() => edit(row)}>编辑</button>
            <button class="link-btn danger" on:click={() => remove(row)}>删除</button>
          </td>
        </tr>
      {:else}
        <tr><td colspan="8">暂无数据</td></tr>
      {/each}
    </tbody>
  </table>
</section>

<style>
  .filters {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem;
    align-items: flex-end;
  }

  .filters label {
    display: grid;
    gap: 0.3rem;
    font-size: 0.8rem;
    color: var(--steel);
  }

  .filters select {
    border: 1px solid var(--line);
    background: rgba(0, 0, 0, 0.35);
    color: white;
    padding: 0.55rem 0.65rem;
    min-width: 160px;
  }

  .detail {
    border-color: rgba(231, 76, 60, 0.35);
  }

  .detail-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0.7rem 1rem;
    margin-bottom: 0.9rem;
  }

  .detail-grid div {
    display: grid;
    gap: 0.2rem;
    font-size: 0.85rem;
  }

  .note-edit {
    margin-bottom: 0.4rem;
  }

  .btn-danger {
    border: none;
    background: transparent;
    color: var(--vermillion-400);
    border: 1px solid var(--vermillion-700);
    padding: 0.55rem 1rem;
    cursor: pointer;
  }

  .btn-danger:hover {
    background: rgba(192, 57, 43, 0.2);
  }

  tr.row-active {
    background: rgba(192, 57, 43, 0.12);
  }

  @media (max-width: 900px) {
    .detail-grid {
      grid-template-columns: 1fr 1fr;
    }
  }
</style>
