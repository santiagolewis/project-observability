<script setup>
import { ref, watch } from "vue";
import { getIncidents, getIncidentDetail, updateIncident } from "../services/api";

const props = defineProps({
  datasetId: { type: String, required: true },
  refreshKey: { type: Number, default: 0 },
});

const incidents = ref([]);
const loading = ref(false);
const error = ref(null);
const expandedId = ref(null);
const expandedAlerts = ref([]);

const STATUSES = ["open", "acknowledged", "resolved", "muted"];

async function load() {
  loading.value = true;
  error.value = null;
  try {
    incidents.value = await getIncidents(props.datasetId);
  } catch (e) {
    error.value = e.message || "Could not load incidents";
  } finally {
    loading.value = false;
  }
}

async function toggle(incident) {
  if (expandedId.value === incident.id) {
    expandedId.value = null;
    expandedAlerts.value = [];
    return;
  }
  expandedId.value = incident.id;
  expandedAlerts.value = [];
  try {
    const detail = await getIncidentDetail(props.datasetId, incident.id);
    expandedAlerts.value = detail.alerts || [];
  } catch {
    expandedAlerts.value = [];
  }
}

async function changeStatus(incident, status) {
  try {
    const updated = await updateIncident(props.datasetId, incident.id, { status });
    Object.assign(incident, updated);
  } catch (e) {
    error.value = e.message || "Could not update incident";
  }
}

async function setAssignee(incident, event) {
  const assignee = event.target.value.trim();
  try {
    const updated = await updateIncident(props.datasetId, incident.id, { assignee });
    Object.assign(incident, updated);
  } catch (e) {
    error.value = e.message || "Could not update assignee";
  }
}

function fmtDate(value) {
  if (!value) return "—";
  return new Date(value).toLocaleString();
}

watch(() => [props.datasetId, props.refreshKey], load, { immediate: true });
</script>

<template>
  <div class="card pad">
    <h3 class="section-title">
      Incidents <span class="badge">{{ incidents.length }}</span>
    </h3>
    <p class="muted section-sub">
      Alerts are grouped into incidents. Acknowledge, resolve or mute to manage noise.
    </p>

    <div v-if="error" class="error-msg">{{ error }}</div>
    <p v-if="loading" class="muted empty">Loading incidents…</p>
    <p v-else-if="!incidents.length" class="muted empty">
      No incidents. Nothing to triage.
    </p>

    <ul v-else class="incidents">
      <li v-for="inc in incidents" :key="inc.id" class="incident">
        <div class="incident-row" @click="toggle(inc)">
          <div class="incident-main">
            <span :class="['severity', inc.severity]">{{ inc.severity }}</span>
            <div class="incident-text">
              <span class="incident-title">{{ inc.title }}</span>
              <span class="incident-meta muted">
                Opened {{ fmtDate(inc.created_at) }}
                <template v-if="inc.assignee"> · {{ inc.assignee }}</template>
              </span>
            </div>
          </div>
          <span :class="['inc-status', inc.status]">{{ inc.status }}</span>
        </div>

        <div v-if="expandedId === inc.id" class="incident-detail">
          <div class="detail-controls">
            <label class="ctrl">
              <span class="muted">Status</span>
              <select
                class="input input-sm"
                :value="inc.status"
                @change="changeStatus(inc, $event.target.value)"
              >
                <option v-for="s in STATUSES" :key="s" :value="s">{{ s }}</option>
              </select>
            </label>
            <label class="ctrl">
              <span class="muted">Assignee</span>
              <input
                class="input input-sm"
                :value="inc.assignee || ''"
                placeholder="unassigned"
                @change="setAssignee(inc, $event)"
              />
            </label>
          </div>

          <p class="muted alerts-label">Grouped alerts ({{ expandedAlerts.length }})</p>
          <ul class="inc-alerts">
            <li v-for="a in expandedAlerts" :key="a.id" class="inc-alert">
              <span :class="['severity', a.severity]">{{ a.severity }}</span>
              <span class="inc-alert-msg">{{ a.message }}</span>
            </li>
          </ul>
        </div>
      </li>
    </ul>
  </div>
</template>

<style scoped>
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
.pad {
  padding: 20px;
}
.empty {
  font-size: 0.86rem;
  margin: 8px 0 0;
}
.error-msg {
  color: var(--critical);
  font-size: 0.84rem;
  margin-bottom: 8px;
}

.incidents {
  list-style: none;
  margin: 8px 0 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.incident {
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.incident-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 11px 12px;
  cursor: pointer;
  transition: background 0.12s ease;
}
.incident-row:hover {
  background: var(--surface-muted);
}

.incident-main {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.incident-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.incident-title {
  font-weight: 600;
  font-size: 0.88rem;
}

.incident-meta {
  font-size: 0.76rem;
}

.inc-status {
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  padding: 3px 9px;
  border-radius: 999px;
  white-space: nowrap;
}
.inc-status.open {
  color: var(--critical);
  background: var(--critical-soft);
}
.inc-status.acknowledged {
  color: var(--warning);
  background: var(--warning-soft);
}
.inc-status.resolved {
  color: var(--healthy);
  background: var(--healthy-soft);
}
.inc-status.muted {
  color: var(--learning);
  background: var(--learning-soft);
}

.incident-detail {
  padding: 12px;
  border-top: 1px solid var(--border);
  background: var(--surface-muted);
}

.detail-controls {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.ctrl {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 0.74rem;
  font-weight: 600;
}

.input-sm {
  padding: 6px 9px;
  font-size: 0.82rem;
}

.alerts-label {
  font-size: 0.76rem;
  font-weight: 600;
  margin: 0 0 6px;
}

.inc-alerts {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.inc-alert {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.inc-alert-msg {
  font-size: 0.82rem;
}
</style>
