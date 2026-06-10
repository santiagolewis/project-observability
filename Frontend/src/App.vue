<script setup>
import { ref } from "vue";
import DatasetList from "./Components/DatasetList.vue";
import CreateDataset from "./Components/CreateDataset.vue";
import DatasetDetail from "./Components/DatasetDetail.vue";

const selectedDataset = ref(null);
const showCreate = ref(false);
// Bumping this key forces the list to reload (after create / upload).
const listRefreshKey = ref(0);

function handleCreated(dataset) {
  showCreate.value = false;
  listRefreshKey.value++;
  if (dataset && dataset.id) {
    selectedDataset.value = dataset;
  }
}

function refreshList() {
  listRefreshKey.value++;
}
</script>

<template>
  <div class="app">
    <header class="topbar">
      <div class="brand">
        <div class="brand-mark">◎</div>
        <div>
          <h1>Data Observability</h1>
          <p class="muted brand-sub">Monitor dataset health, runs &amp; anomalies</p>
        </div>
      </div>
      <button class="btn btn-primary" @click="showCreate = true">
        <span>+</span> New dataset
      </button>
    </header>

    <main class="layout">
      <aside class="sidebar">
        <DatasetList
          :refresh-key="listRefreshKey"
          :selected-id="selectedDataset?.id"
          @selectDataset="selectedDataset = $event"
        />
      </aside>

      <section class="content">
        <DatasetDetail
          v-if="selectedDataset"
          :dataset="selectedDataset"
          @uploaded="refreshList"
        />
        <div v-else class="empty-state card">
          <div class="empty-icon">📊</div>
          <h2>Select a dataset</h2>
          <p class="muted">
            Pick a dataset from the left to view its health, runs and alerts —
            or create a new one to get started.
          </p>
          <button class="btn btn-primary" @click="showCreate = true">
            + Create your first dataset
          </button>
        </div>
      </section>
    </main>

    <CreateDataset
      v-if="showCreate"
      @close="showCreate = false"
      @created="handleCreated"
    />
  </div>
</template>

<style scoped>
.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 28px;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  z-index: 10;
}

.brand {
  display: flex;
  align-items: center;
  gap: 14px;
}

.brand-mark {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  font-size: 1.4rem;
  color: #fff;
  background: linear-gradient(135deg, #6366f1, #4f46e5);
  box-shadow: var(--shadow-md);
}

.brand h1 {
  font-size: 1.15rem;
}

.brand-sub {
  font-size: 0.8rem;
  margin: 2px 0 0;
}

.layout {
  flex: 1;
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 24px;
  padding: 24px 28px;
  max-width: 1280px;
  width: 100%;
  margin: 0 auto;
}

.sidebar {
  min-width: 0;
}

.content {
  min-width: 0;
}

.empty-state {
  padding: 64px 32px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.empty-icon {
  font-size: 2.6rem;
  margin-bottom: 4px;
}

.empty-state p {
  max-width: 380px;
  margin: 0 0 12px;
}

@media (max-width: 860px) {
  .layout {
    grid-template-columns: 1fr;
  }
}
</style>
