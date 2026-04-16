<script setup>
import { ref, onMounted } from "vue";
import { getDatasets } from "../services/api";

const emit = defineEmits(["selectDataset"]);
const datasets = ref([]);

onMounted(async () => {
  datasets.value = await getDatasets();
});
</script>

<template>
  <div>
    <h2>Datasets</h2>

    <ul>
      <li
        v-for="ds in datasets"
        :key="ds.id"
        @click="emit('selectDataset', ds)"
        style="cursor: pointer"
      >
        <strong>{{ ds.name }}</strong> - {{ ds.description }}
      </li>
    </ul>
  </div>
</template>
