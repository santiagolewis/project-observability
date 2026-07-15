<script setup>
import { computed } from "vue";

const props = defineProps({
  points: { type: Array, default: () => [] },
});

const W = 280;
const H = 64;
const PAD = 6;

const metrics = [
  { key: "row_count", label: "Row count", format: (v) => v?.toLocaleString() ?? "—" },
  {
    key: "avg_null_pct",
    label: "Avg null rate",
    format: (v) => (v === null || v === undefined ? "—" : `${(v * 100).toFixed(1)}%`),
  },
  { key: "column_count", label: "Columns", format: (v) => v ?? "—" },
  { key: "alert_count", label: "Alerts / run", format: (v) => v ?? "0" },
];

function buildSeries(key) {
  const values = props.points.map((p) => (p[key] == null ? null : Number(p[key])));
  const present = values.filter((v) => v !== null);
  if (!present.length) return { path: "", area: "", last: null, dot: null };

  const min = Math.min(...present);
  const max = Math.max(...present);
  const span = max - min || 1;
  const n = values.length;
  const stepX = n > 1 ? (W - PAD * 2) / (n - 1) : 0;

  const coords = values.map((v, i) => {
    const x = PAD + stepX * i;
    const y =
      v === null ? null : H - PAD - ((v - min) / span) * (H - PAD * 2);
    return { x, y };
  });

  const valid = coords.filter((c) => c.y !== null);
  const path = valid
    .map((c, i) => `${i === 0 ? "M" : "L"}${c.x.toFixed(1)},${c.y.toFixed(1)}`)
    .join(" ");
  const area =
    valid.length > 1
      ? `${path} L${valid[valid.length - 1].x.toFixed(1)},${H - PAD} L${valid[0].x.toFixed(
          1,
        )},${H - PAD} Z`
      : "";
  const lastVal = present[present.length - 1];
  const dot = valid.length ? valid[valid.length - 1] : null;
  return { path, area, last: lastVal, dot };
}

const series = computed(() =>
  metrics.map((m) => ({ ...m, ...buildSeries(m.key) })),
);

const hasData = computed(() => props.points.length > 0);
</script>

<template>
  <div v-if="!hasData" class="muted empty">No history yet — upload a few runs to see trends.</div>
  <div v-else class="trend-grid">
    <div v-for="s in series" :key="s.key" class="trend">
      <div class="trend-head">
        <span class="trend-label">{{ s.label }}</span>
        <span class="trend-last">{{ s.format(s.last) }}</span>
      </div>
      <svg :viewBox="`0 0 ${W} ${H}`" class="spark" preserveAspectRatio="none">
        <path v-if="s.area" :d="s.area" class="spark-area" />
        <path v-if="s.path" :d="s.path" class="spark-line" />
        <circle v-if="s.dot" :cx="s.dot.x" :cy="s.dot.y" r="2.5" class="spark-dot" />
      </svg>
    </div>
  </div>
</template>

<style scoped>
.empty {
  font-size: 0.86rem;
  margin: 8px 0 0;
}

.trend-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-top: 8px;
}

.trend {
  background: var(--surface-muted);
  border-radius: var(--radius-sm);
  padding: 12px;
}

.trend-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 6px;
}

.trend-label {
  font-size: 0.76rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--text-muted);
}

.trend-last {
  font-size: 0.95rem;
  font-weight: 700;
}

.spark {
  width: 100%;
  height: 56px;
  display: block;
}

.spark-line {
  fill: none;
  stroke: var(--primary);
  stroke-width: 2;
  stroke-linejoin: round;
  stroke-linecap: round;
  vector-effect: non-scaling-stroke;
}

.spark-area {
  fill: var(--primary-soft);
  opacity: 0.7;
}

.spark-dot {
  fill: var(--primary);
}

@media (max-width: 720px) {
  .trend-grid {
    grid-template-columns: 1fr;
  }
}
</style>
