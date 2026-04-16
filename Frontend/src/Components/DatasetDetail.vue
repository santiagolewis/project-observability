<script setup>
import { ref, onMounted, watch } from "vue";
import { getRuns, getAlerts } from "../services/api";

const props = defineProps({
  dataset: Object,
});

const runs = ref([]);
const alerts = ref([]);

async function loadData() {
  runs.value = await getRuns(props.dataset.id);
  alerts.value = await getAlerts(props.dataset.id);
}

watch(() => props.dataset, loadData, { immediate: true });
</script>

<template>
  <div>
    <h2>Detalle: {{ dataset.name }}</h2>

    <h3>Runs</h3>
    <ul>
      <li v-for="run in runs" :key="run.id">Run ID: {{ run.id }}</li>
    </ul>

    <h3>Alertas</h3>
    <ul>
      <li v-for="alert in alerts" :key="alert.id">⚠️ {{ alert.message }}</li>
    </ul>
  </div>
</template>
