<script setup>
import { ref } from "vue";
import { createDataset } from "../services/api";

const emit = defineEmits(["close", "created"]);

const name = ref("");
const description = ref("");
const submitting = ref(false);
const error = ref(null);

async function handleSubmit() {
  if (!name.value.trim()) {
    error.value = "Name is required.";
    return;
  }
  submitting.value = true;
  error.value = null;
  try {
    const dataset = await createDataset({
      name: name.value.trim(),
      description: description.value.trim(),
    });
    emit("created", dataset);
  } catch (e) {
    error.value = e.message || "Could not create dataset";
  } finally {
    submitting.value = false;
  }
}
</script>

<template>
  <div class="overlay" @click.self="emit('close')">
    <div class="modal card">
      <div class="modal-head">
        <h2>Create dataset</h2>
        <button class="close" @click="emit('close')" aria-label="Close">×</button>
      </div>

      <form class="modal-body" @submit.prevent="handleSubmit">
        <div class="field">
          <label for="ds-name">Name</label>
          <input
            id="ds-name"
            class="input"
            v-model="name"
            placeholder="e.g. Orders daily export"
            autofocus
          />
        </div>

        <div class="field">
          <label for="ds-desc">Description <span class="muted">(optional)</span></label>
          <textarea
            id="ds-desc"
            class="input"
            v-model="description"
            rows="3"
            placeholder="What does this dataset track?"
          ></textarea>
        </div>

        <p v-if="error" class="error">{{ error }}</p>

        <div class="modal-actions">
          <button type="button" class="btn btn-ghost" @click="emit('close')">
            Cancel
          </button>
          <button type="submit" class="btn btn-primary" :disabled="submitting">
            <span v-if="submitting" class="spinner"></span>
            {{ submitting ? "Creating…" : "Create dataset" }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  backdrop-filter: blur(2px);
  display: grid;
  place-items: center;
  padding: 20px;
  z-index: 50;
  animation: fade 0.12s ease;
}

@keyframes fade {
  from {
    opacity: 0;
  }
}

.modal {
  width: 100%;
  max-width: 440px;
  box-shadow: var(--shadow-lg);
  animation: pop 0.14s ease;
}

@keyframes pop {
  from {
    transform: translateY(8px) scale(0.98);
    opacity: 0;
  }
}

.modal-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 20px;
  border-bottom: 1px solid var(--border);
}

.modal-head h2 {
  font-size: 1.05rem;
}

.close {
  border: none;
  background: transparent;
  font-size: 1.5rem;
  line-height: 1;
  color: var(--text-muted);
  padding: 0 4px;
}
.close:hover {
  color: var(--text);
}

.modal-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 4px;
}

.error {
  color: var(--critical);
  font-size: 0.85rem;
  margin: 0;
}
</style>
