<script setup>
import { ref } from "vue";
import DatasetList from "./Components/DatasetList.vue";
import CreateDataset from "./Components/CreateDataset.vue";
import DatasetDetail from "./Components/DatasetDetail.vue";
const selectedDataset = ref(null);
</script>

<template>
  <div>
    <h1>Data Observability Platform</h1>

    <DatasetList @selectDataset="selectedDataset = $event" />

    <DatasetDetail v-if="selectedDataset" :dataset="selectedDataset" />
  </div>
</template>
