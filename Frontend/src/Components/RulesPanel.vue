<script setup>
import { ref, watch, computed } from "vue";
import { getRules, createRule, deleteRule, updateRule } from "../services/api";

const props = defineProps({
  datasetId: { type: String, required: true },
});

const rules = ref([]);
const loading = ref(false);
const error = ref(null);
const showForm = ref(false);
const submitting = ref(false);

const RULE_TYPES = [
  { value: "column_required", label: "Column required", needsColumn: true, config: "none" },
  { value: "not_null", label: "Not null (max null %)", needsColumn: true, config: "max_null_pct" },
  { value: "min_value", label: "Minimum value", needsColumn: true, config: "value" },
  { value: "max_value", label: "Maximum value", needsColumn: true, config: "value" },
  { value: "accepted_values", label: "Accepted values", needsColumn: true, config: "values" },
  { value: "unique", label: "Unique", needsColumn: true, config: "none" },
  { value: "regex", label: "Regex pattern", needsColumn: true, config: "pattern" },
];

const form = ref({
  rule_type: "column_required",
  column_name: "",
  severity: "high",
  value: "",
  max_null_pct: "",
  values: "",
  pattern: "",
});

const currentType = computed(() =>
  RULE_TYPES.find((t) => t.value === form.value.rule_type),
);

async function load() {
  loading.value = true;
  error.value = null;
  try {
    rules.value = await getRules(props.datasetId);
  } catch (e) {
    error.value = e.message || "Could not load rules";
  } finally {
    loading.value = false;
  }
}

function buildConfig() {
  const kind = currentType.value?.config;
  if (kind === "value") return { value: Number(form.value.value) };
  if (kind === "max_null_pct")
    return { max_null_pct: Number(form.value.max_null_pct) / 100 };
  if (kind === "pattern") return { pattern: form.value.pattern };
  if (kind === "values")
    return {
      values: form.value.values
        .split(",")
        .map((v) => v.trim())
        .filter(Boolean),
    };
  return {};
}

async function submit() {
  if (!form.value.column_name.trim()) {
    error.value = "Column name is required.";
    return;
  }
  submitting.value = true;
  error.value = null;
  try {
    await createRule(props.datasetId, {
      rule_type: form.value.rule_type,
      column_name: form.value.column_name.trim(),
      severity: form.value.severity,
      config: buildConfig(),
      is_active: true,
    });
    resetForm();
    showForm.value = false;
    await load();
  } catch (e) {
    error.value = e.message || "Could not create rule";
  } finally {
    submitting.value = false;
  }
}

function resetForm() {
  form.value = {
    rule_type: "column_required",
    column_name: "",
    severity: "high",
    value: "",
    max_null_pct: "",
    values: "",
    pattern: "",
  };
}

async function remove(rule) {
  try {
    await deleteRule(props.datasetId, rule.id);
    await load();
  } catch (e) {
    error.value = e.message || "Could not delete rule";
  }
}

async function toggleActive(rule) {
  try {
    const updated = await updateRule(props.datasetId, rule.id, {
      is_active: !rule.is_active,
    });
    Object.assign(rule, updated);
  } catch (e) {
    error.value = e.message || "Could not update rule";
  }
}

function ruleLabel(rule) {
  const t = RULE_TYPES.find((x) => x.value === rule.rule_type);
  return t ? t.label : rule.rule_type;
}

function ruleSummary(rule) {
  const c = rule.config || {};
  if (rule.rule_type === "not_null" && c.max_null_pct != null)
    return `≤ ${(c.max_null_pct * 100).toFixed(1)}% null`;
  if (rule.rule_type === "min_value") return `≥ ${c.value}`;
  if (rule.rule_type === "max_value") return `≤ ${c.value}`;
  if (rule.rule_type === "accepted_values")
    return `in [${(c.values || []).join(", ")}]`;
  if (rule.rule_type === "regex") return `/${c.pattern}/`;
  return "";
}

watch(() => props.datasetId, load, { immediate: true });
</script>

<template>
  <div class="card pad">
    <div class="rules-head">
      <h3 class="section-title">
        Rules <span class="badge">{{ rules.length }}</span>
      </h3>
      <button class="btn btn-ghost btn-sm" @click="showForm = !showForm">
        {{ showForm ? "Cancel" : "+ Add rule" }}
      </button>
    </div>
    <p class="muted section-sub">
      Configurable expectations checked on every upload.
    </p>

    <div v-if="showForm" class="rule-form">
      <div class="form-grid">
        <label class="field">
          <span>Type</span>
          <select class="input input-sm" v-model="form.rule_type">
            <option v-for="t in RULE_TYPES" :key="t.value" :value="t.value">
              {{ t.label }}
            </option>
          </select>
        </label>
        <label class="field">
          <span>Column</span>
          <input class="input input-sm" v-model="form.column_name" placeholder="column name" />
        </label>
        <label class="field">
          <span>Severity</span>
          <select class="input input-sm" v-model="form.severity">
            <option value="medium">medium</option>
            <option value="high">high</option>
          </select>
        </label>

        <label v-if="currentType?.config === 'value'" class="field">
          <span>Value</span>
          <input class="input input-sm" type="number" v-model="form.value" />
        </label>
        <label v-if="currentType?.config === 'max_null_pct'" class="field">
          <span>Max null %</span>
          <input class="input input-sm" type="number" min="0" max="100" v-model="form.max_null_pct" />
        </label>
        <label v-if="currentType?.config === 'pattern'" class="field">
          <span>Regex</span>
          <input class="input input-sm" v-model="form.pattern" placeholder="^[A-Z]{3}$" />
        </label>
        <label v-if="currentType?.config === 'values'" class="field wide">
          <span>Accepted values (comma-separated)</span>
          <input class="input input-sm" v-model="form.values" placeholder="A, B, C" />
        </label>
      </div>
      <div class="form-actions">
        <button class="btn btn-primary btn-sm" :disabled="submitting" @click="submit">
          {{ submitting ? "Saving…" : "Save rule" }}
        </button>
      </div>
    </div>

    <div v-if="error" class="error-msg">{{ error }}</div>
    <p v-if="loading" class="muted empty">Loading rules…</p>
    <p v-else-if="!rules.length" class="muted empty">No rules yet.</p>

    <ul v-else class="rules">
      <li v-for="rule in rules" :key="rule.id" :class="['rule', { inactive: !rule.is_active }]">
        <div class="rule-main">
          <span class="rule-col">{{ rule.column_name || "—" }}</span>
          <span class="rule-type">{{ ruleLabel(rule) }}</span>
          <span v-if="ruleSummary(rule)" class="rule-summary muted">{{ ruleSummary(rule) }}</span>
        </div>
        <div class="rule-actions">
          <span :class="['severity', rule.severity]">{{ rule.severity }}</span>
          <button class="icon-btn" :title="rule.is_active ? 'Disable' : 'Enable'" @click="toggleActive(rule)">
            {{ rule.is_active ? "⏸" : "▶" }}
          </button>
          <button class="icon-btn danger" title="Delete" @click="remove(rule)">×</button>
        </div>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.pad {
  padding: 20px;
}
.rules-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.section-title {
  font-size: 1rem;
  display: flex;
  align-items: center;
  gap: 8px;
}
.section-sub {
  margin: 4px 0 14px;
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
.empty {
  font-size: 0.86rem;
  margin: 8px 0 0;
}
.error-msg {
  color: var(--critical);
  font-size: 0.84rem;
  margin: 8px 0;
}

.rule-form {
  background: var(--surface-muted);
  border-radius: var(--radius-sm);
  padding: 14px;
  margin-bottom: 14px;
}
.form-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 0.74rem;
  font-weight: 600;
  color: var(--text-muted);
}
.field.wide {
  grid-column: 1 / -1;
}
.input-sm {
  padding: 6px 9px;
  font-size: 0.82rem;
}
.form-actions {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}

.rules {
  list-style: none;
  margin: 8px 0 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.rule {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  background: var(--surface-muted);
}
.rule.inactive {
  opacity: 0.55;
}
.rule-main {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  flex-wrap: wrap;
}
.rule-col {
  font-weight: 700;
  font-size: 0.85rem;
}
.rule-type {
  font-size: 0.82rem;
}
.rule-summary {
  font-size: 0.78rem;
}
.rule-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.icon-btn {
  border: 1px solid var(--border);
  background: var(--surface);
  border-radius: 6px;
  width: 26px;
  height: 26px;
  font-size: 0.85rem;
  line-height: 1;
  color: var(--text-muted);
}
.icon-btn:hover {
  background: var(--surface-muted);
}
.icon-btn.danger:hover {
  color: var(--critical);
  border-color: var(--critical);
}

@media (max-width: 720px) {
  .form-grid {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
