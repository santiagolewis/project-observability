<script setup>
import { ref, onMounted } from "vue";
import { getDatasets, getDatasetStatus } from "../services/api";

const emit = defineEmits(["selectDataset"]);
const datasets = ref([]);

onMounted(async () => {
  const data = await getDatasets();

  for (let d of data) {
    try {
      const statusRes = await getDatasetStatus(d.id);
      d.status = statusRes.status;
    } catch (e) {
      console.error("Error obteniendo status:", e);
      d.status = "unknown";
    }
  }

  datasets.value = data;
});

function getColor(status) {
  if (status === "critical") return "red";
  if (status === "warning") return "orange";
  if (status === "unknown") return "gray";
  return "green";
}
</script>

<template>
  <div>
    <h2>Datasets</h2>

    <ul>
      <li v-for="d in datasets" :key="d.id" @click="$emit('selectDataset', d)">
        {{ d.name }} - {{ d.description }}

        <span
          :style="{
            color: getColor(d.status),
            marginLeft: '8px',
            fontWeight: 'bold',
          }"
        >
          ● {{ d.status }}
        </span>
      </li>
    </ul>
  </div>
</template>
