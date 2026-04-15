<script setup>
import { ref } from "vue";
import { createDataset } from "../services/api";

const name = ref("");
const description = ref("");

async function handleSubmit() {
  await createDataset({
    name: name.value,
    description: description.value,
  });

  name.value = "";
  description.value = "";
}
</script>

<template>
  <div>
    <h2>Create Dataset</h2>
    <input v-model="name" placeholder="Name" />
    <input v-model="description" placeholder="Description" />
    <button @click="handleSubmit">Create</button>
  </div>
</template>
