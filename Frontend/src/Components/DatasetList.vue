<script setup>
import { ref, onMounted } from "vue";
import { getDatasets } from "../services/api";

const datasets = ref([]);

onMounted(async () => {
  datasets.value = await getDatasets();
});
</script>

<template>
  <div>
    <h2>Datasets</h2>

    <div v-if="datasets.length === 0">No hay datasets</div>

    <ul>
      <li v-for="ds in datasets" :key="ds.id">
        <strong>{{ ds.name }}</strong> - {{ ds.description }}
      </li>
    </ul>
  </div>
</template>
