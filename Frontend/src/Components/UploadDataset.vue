<script setup>
import { ref } from "vue";
import { uploadDataset } from "../services/api";

const props = defineProps({
  datasetId: { type: String, required: true },
});
const emit = defineEmits(["uploaded"]);

const fileInput = ref(null);
const dragging = ref(false);
const uploading = ref(false);
const result = ref(null); // { type: 'success' | 'error', message }

const ACCEPTED = ".csv,.tsv,.txt,.xlsx,.xls,.xlsm";

function pickFile() {
  fileInput.value?.click();
}

async function handleFiles(files) {
  if (!files || !files.length) return;
  const file = files[0];
  uploading.value = true;
  result.value = null;
  try {
    const res = await uploadDataset(props.datasetId, file);
    result.value = {
      type: "success",
      message: `“${file.name}” processed — ${res.alerts_created} alert(s) generated.`,
    };
    emit("uploaded", res);
  } catch (e) {
    result.value = {
      type: "error",
      message: e.message || "Upload failed.",
    };
  } finally {
    uploading.value = false;
    if (fileInput.value) fileInput.value.value = "";
  }
}

function onDrop(e) {
  dragging.value = false;
  handleFiles(e.dataTransfer.files);
}

function onInputChange(e) {
  handleFiles(e.target.files);
}
</script>

<template>
  <div class="upload">
    <div
      :class="['dropzone', { dragging, busy: uploading }]"
      @click="pickFile"
      @dragover.prevent="dragging = true"
      @dragleave.prevent="dragging = false"
      @drop.prevent="onDrop"
    >
      <input
        ref="fileInput"
        type="file"
        :accept="ACCEPTED"
        class="hidden-input"
        @change="onInputChange"
      />

      <template v-if="uploading">
        <div class="dz-spinner"></div>
        <p class="dz-title">Processing dataset…</p>
      </template>
      <template v-else>
        <div class="dz-icon">⬆</div>
        <p class="dz-title">Drop a file here or <span class="link">browse</span></p>
        <p class="dz-hint muted">CSV, TSV or Excel (.xlsx, .xls)</p>
      </template>
    </div>

    <div v-if="result" :class="['result', result.type]">
      <span class="result-icon">{{ result.type === "success" ? "✓" : "!" }}</span>
      <span>{{ result.message }}</span>
    </div>
  </div>
</template>

<style scoped>
.upload {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.dropzone {
  border: 2px dashed var(--border);
  border-radius: var(--radius);
  padding: 28px 20px;
  text-align: center;
  cursor: pointer;
  background: var(--surface-muted);
  transition: border-color 0.15s ease, background 0.15s ease;
}

.dropzone:hover,
.dropzone.dragging {
  border-color: var(--primary);
  background: var(--primary-soft);
}

.dropzone.busy {
  cursor: progress;
  pointer-events: none;
}

.hidden-input {
  display: none;
}

.dz-icon {
  font-size: 1.6rem;
  color: var(--primary);
  margin-bottom: 6px;
}

.dz-title {
  margin: 0;
  font-weight: 600;
  font-size: 0.92rem;
}

.dz-hint {
  margin: 4px 0 0;
  font-size: 0.8rem;
}

.link {
  color: var(--primary);
  text-decoration: underline;
}

.dz-spinner {
  width: 26px;
  height: 26px;
  margin: 0 auto 8px;
  border: 3px solid #c7d2fe;
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

.result {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 0.85rem;
  padding: 10px 12px;
  border-radius: var(--radius-sm);
}

.result.success {
  color: var(--healthy);
  background: var(--healthy-soft);
}

.result.error {
  color: var(--critical);
  background: var(--critical-soft);
}

.result-icon {
  font-weight: 800;
}
</style>
