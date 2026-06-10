<script setup>
import { ref, watch } from "vue";
import { getRuns, getAlerts, getDatasetSummary, getDatasetStatus } from "../services/api";
import UploadDataset from "./UploadDataset.vue";

const props = defineProps({
  dataset: Object,
});
const emit = defineEmits(["uploaded"]);

const runs = ref([]);
const alerts = ref([]);
const summary = ref(null);
const status = ref(null);
const loading = ref(false);
const error = ref(null);

async function loadData() {
  loading.value = true;
  error.value = null;
  try {
    const [runsRes, alertsRes, summaryRes, statusRes] = await Promise.all([
      getRuns(props.dataset.id),
      getAlerts(props.dataset.id),
      getDatasetSummary(props.dataset.id).catch(() => null),
      getDatasetStatus(props.dataset.id).catch(() => null),
    ]);
    runs.value = runsRes;
    alerts.value = alertsRes;
    summary.value = summaryRes;
    status.value = statusRes;
  } catch (e) {
    error.value = e.message || "Could not load dataset details";
  } finally {
    loading.value = false;
  }
}

function onUploaded(res) {
  loadData();
  emit("uploaded", res);
}

function fmtPct(value) {
  if (value === null || value === undefined) return "—";
  return `${(value * 100).toFixed(1)}%`;
}

function fmtNumber(value) {
  if (value === null || value === undefined) return "—";
  return value.toLocaleString();
}

function fmtDelta(value) {
  if (value === null || value === undefined) return null;
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(1)}%`;
}

function fmtDate(value) {
  if (!value) return "—";
  const d = new Date(value);
  return d.toLocaleString();
}

watch(() => props.dataset, loadData, { immediate: true });
</script>

<template>
  <div class="detail">
    <div class="detail-head card">
      <div>
        <div class="head-top">
          <h2>{{ dataset.name }}</h2>
          <span :class="['pill', status?.status || 'unknown']">
            <span class="dot"></span>{{ status?.status || "unknown" }}
          </span>
        </div>
        <p class="muted desc" v-if="dataset.description">{{ dataset.description }}</p>
        <p class="muted desc" v-if="status?.message">{{ status.message }}</p>
      </div>
    </div>

    <div v-if="error" class="card pad error">{{ error }}</div>

    <!-- KPI tiles -->
    <div class="kpis" v-if="summary">
      <div class="kpi card">
        <span class="kpi-label">Latest rows</span>
        <span class="kpi-value">{{ fmtNumber(summary.latest_run?.row_count) }}</span>
        <span
          v-if="summary.row_count_delta_pct !== null"
          :class="['kpi-delta', summary.row_count_delta_pct < 0 ? 'down' : 'up']"
        >
          {{ fmtDelta(summary.row_count_delta_pct) }} vs prev
        </span>
      </div>
      <div class="kpi card">
        <span class="kpi-label">Columns</span>
        <span class="kpi-value">{{ fmtNumber(summary.column_count) }}</span>
        <span class="kpi-delta muted">{{ summary.run_count }} run(s)</span>
      </div>
      <div class="kpi card">
        <span class="kpi-label">Avg null rate</span>
        <span class="kpi-value">{{ fmtPct(summary.avg_null_pct) }}</span>
        <span class="kpi-delta muted">
          {{ summary.columns_with_null_increase }} col(s) ↑
        </span>
      </div>
      <div class="kpi card">
        <span class="kpi-label">Alerts</span>
        <span class="kpi-value">{{ fmtNumber(summary.alerts_total) }}</span>
        <span class="kpi-delta muted">{{ summary.alerts_last_24h }} in 24h</span>
      </div>
    </div>

    <!-- Upload -->
    <div class="card pad">
      <h3 class="section-title">Upload a new snapshot</h3>
      <p class="muted section-sub">
        Each upload creates a run and is compared against previous runs to detect anomalies.
      </p>
      <UploadDataset :dataset-id="dataset.id" @uploaded="onUploaded" />
    </div>

    <div class="two-col">
      <!-- Runs -->
      <div class="card pad">
        <h3 class="section-title">Runs <span class="badge">{{ runs.length }}</span></h3>
        <p v-if="!runs.length" class="muted empty">No runs yet — upload a file to begin.</p>
        <ul v-else class="runs">
          <li v-for="run in runs" :key="run.id" class="run">
            <div>
              <span class="run-rows">{{ fmtNumber(run.row_count) }} rows</span>
              <span class="run-date muted">{{ fmtDate(run.created_at) }}</span>
            </div>
            <code class="run-id">{{ run.id.slice(0, 8) }}</code>
          </li>
        </ul>
      </div>

      <!-- Alerts -->
      <div class="card pad">
        <h3 class="section-title">Alerts <span class="badge">{{ alerts.length }}</span></h3>
        <p v-if="!alerts.length" class="muted empty">No alerts. Everything looks healthy.</p>
        <ul v-else class="alerts">
          <li v-for="alert in alerts" :key="alert.id" class="alert">
            <span :class="['severity', alert.severity]">{{ alert.severity }}</span>
            <div class="alert-body">
              <span class="alert-msg">{{ alert.message }}</span>
              <span
                v-if="alert.previous_value || alert.current_value"
                class="alert-meta muted"
              >
                {{ alert.previous_value ?? "—" }} → {{ alert.current_value ?? "—" }}
              </span>
            </div>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<style scoped>
.detail {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.pad {
  padding: 20px;
}

.error {
  color: var(--critical);
}

.detail-head {
  padding: 20px;
}

.head-top {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.head-top h2 {
  font-size: 1.25rem;
}

.desc {
  margin: 6px 0 0;
  font-size: 0.88rem;
}

.kpis {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
}

.kpi {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.kpi-label {
  font-size: 0.76rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--text-muted);
}

.kpi-value {
  font-size: 1.5rem;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.kpi-delta {
  font-size: 0.76rem;
  font-weight: 600;
}
.kpi-delta.down {
  color: var(--critical);
}
.kpi-delta.up {
  color: var(--healthy);
}

.section-title {
  font-size: 1rem;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.section-sub {
  margin: 0 0 14px;
  font-size: 0.84rem;
}

.badge {
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--text-muted);
  background: var(--surface-muted);
  border-radius: 999px;
  padding: 1px 8px;
}

.two-col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.empty {
  font-size: 0.86rem;
  margin: 8px 0 0;
}

.runs,
.alerts {
  list-style: none;
  margin: 8px 0 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 320px;
  overflow-y: auto;
}

.run {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  background: var(--surface-muted);
}

.run-rows {
  font-weight: 600;
  font-size: 0.9rem;
  margin-right: 10px;
}

.run-date {
  font-size: 0.78rem;
}

.run-id {
  font-size: 0.72rem;
  color: var(--text-muted);
  background: var(--surface);
  border: 1px solid var(--border);
  padding: 2px 7px;
  border-radius: 6px;
}

.alert {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  background: var(--surface-muted);
}

.alert-body {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.alert-msg {
  font-size: 0.86rem;
  font-weight: 500;
}

.alert-meta {
  font-size: 0.76rem;
  margin-top: 2px;
}

@media (max-width: 1100px) {
  .kpis {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 720px) {
  .two-col {
    grid-template-columns: 1fr;
  }
}
</style>
