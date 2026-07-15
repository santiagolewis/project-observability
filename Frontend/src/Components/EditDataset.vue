<script setup>
import { ref } from "vue";
import { updateDataset } from "../services/api";

const props = defineProps({
  dataset: { type: Object, required: true },
});
const emit = defineEmits(["close", "saved"]);

const name = ref(props.dataset.name || "");
const description = ref(props.dataset.description || "");
const owner = ref(props.dataset.owner || "");
const team = ref(props.dataset.team || "");
const domain = ref(props.dataset.domain || "");
const criticality = ref(props.dataset.criticality || "medium");
const expectedFreshness = ref(props.dataset.expected_freshness_hours ?? "");
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
    const updated = await updateDataset(props.dataset.id, {
      name: name.value.trim(),
      description: description.value.trim() || null,
      owner: owner.value.trim() || null,
      team: team.value.trim() || null,
      domain: domain.value.trim() || null,
      criticality: criticality.value,
      expected_freshness_hours: expectedFreshness.value
        ? Number(expectedFreshness.value)
        : null,
    });
    emit("saved", updated);
  } catch (e) {
    error.value = e.message || "Could not update dataset";
  } finally {
    submitting.value = false;
  }
}
</script>

<template>
  <div class="overlay" @click.self="emit('close')">
    <div class="modal card">
      <div class="modal-head">
        <h2>Edit dataset</h2>
        <button class="close" @click="emit('close')" aria-label="Close">×</button>
      </div>

      <form class="modal-body" @submit.prevent="handleSubmit">
        <div class="field">
          <label>Name</label>
          <input class="input" v-model="name" />
        </div>
        <div class="field">
          <label>Description</label>
          <textarea class="input" v-model="description" rows="2"></textarea>
        </div>
        <div class="grid-2">
          <div class="field">
            <label>Owner</label>
            <input class="input" v-model="owner" />
          </div>
          <div class="field">
            <label>Team</label>
            <input class="input" v-model="team" />
          </div>
        </div>
        <div class="grid-2">
          <div class="field">
            <label>Domain</label>
            <input class="input" v-model="domain" />
          </div>
          <div class="field">
            <label>Criticality</label>
            <select class="input" v-model="criticality">
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
          </div>
        </div>
        <div class="field">
          <label>Expected update frequency <span class="muted">(hours)</span></label>
          <input class="input" type="number" min="1" v-model="expectedFreshness" />
        </div>

        <p v-if="error" class="error">{{ error }}</p>

        <div class="modal-actions">
          <button type="button" class="btn btn-ghost" @click="emit('close')">Cancel</button>
          <button type="submit" class="btn btn-primary" :disabled="submitting">
            <span v-if="submitting" class="spinner"></span>
            {{ submitting ? "Saving…" : "Save changes" }}
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
}
.modal {
  width: 100%;
  max-width: 460px;
  box-shadow: var(--shadow-lg);
  max-height: 90vh;
  overflow-y: auto;
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
}
.modal-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
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
