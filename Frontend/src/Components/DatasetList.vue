<script setup>
import { ref, watch } from "vue";
import { getDatasets, getDatasetStatus } from "../services/api";

const props = defineProps({
  refreshKey: { type: Number, default: 0 },
  selectedId: { type: String, default: null },
});
const emit = defineEmits(["selectDataset"]);

const datasets = ref([]);
const loading = ref(false);
const error = ref(null);

async function load() {
  loading.value = true;
  error.value = null;
  try {
    const data = await getDatasets();
    await Promise.all(
      data.map(async (d) => {
        try {
          const statusRes = await getDatasetStatus(d.id);
          d.status = statusRes.status;
        } catch (e) {
          d.status = "unknown";
        }
      }),
    );
    datasets.value = data;
  } catch (e) {
    error.value = e.message || "Could not load datasets";
  } finally {
    loading.value = false;
  }
}

watch(() => props.refreshKey, load, { immediate: true });
</script>

<template>
  <div class="card list-card">
    <div class="list-head">
      <h2>Datasets</h2>
      <span class="count" v-if="datasets.length">{{ datasets.length }}</span>
    </div>

    <div v-if="loading" class="list-msg muted">Loading datasets…</div>
    <div v-else-if="error" class="list-msg error">{{ error }}</div>
    <div v-else-if="!datasets.length" class="list-msg muted">
      No datasets yet.
    </div>

    <ul v-else class="list">
      <li
        v-for="d in datasets"
        :key="d.id"
        :class="['list-item', { active: d.id === selectedId }]"
        @click="emit('selectDataset', d)"
      >
        <div class="item-main">
          <span class="item-name">{{ d.name }}</span>
          <span v-if="d.description" class="item-desc muted">{{ d.description }}</span>
        </div>
        <span :class="['pill', d.status || 'unknown']">
          <span class="dot"></span>{{ d.status || "unknown" }}
        </span>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.list-card {
  padding: 16px;
  position: sticky;
  top: 90px;
}

.list-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.list-head h2 {
  font-size: 0.95rem;
}

.count {
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--text-muted);
  background: var(--surface-muted);
  border-radius: 999px;
  padding: 2px 9px;
}

.list-msg {
  padding: 18px 6px;
  font-size: 0.88rem;
}
.list-msg.error {
  color: var(--critical);
}

.list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.list-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 11px 12px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background 0.12s ease;
  border: 1px solid transparent;
}

.list-item:hover {
  background: var(--surface-muted);
}

.list-item.active {
  background: var(--primary-soft);
  border-color: #c7d2fe;
}

.item-main {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.item-name {
  font-weight: 600;
  font-size: 0.9rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-desc {
  font-size: 0.78rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
