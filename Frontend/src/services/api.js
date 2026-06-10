const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function handleResponse(res) {
  if (!res.ok) {
    let detail = `Request failed with status ${res.status}`;
    try {
      const body = await res.json();
      if (body && body.detail) {
        detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
      }
    } catch {
      // ignore parse errors, fall back to default message
    }
    throw new Error(detail);
  }
  return res.json();
}

export async function getDatasets() {
  const res = await fetch(`${API_URL}/datasets`);
  return handleResponse(res);
}

export async function createDataset(data) {
  const params = new URLSearchParams({ name: data.name });
  if (data.description) params.append("description", data.description);
  const res = await fetch(`${API_URL}/datasets?${params.toString()}`, {
    method: "POST",
  });
  return handleResponse(res);
}

export async function uploadDataset(datasetId, file) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_URL}/datasets/${datasetId}/upload`, {
    method: "POST",
    body: formData,
  });
  return handleResponse(res);
}

export async function getAlerts(datasetId) {
  const res = await fetch(`${API_URL}/datasets/${datasetId}/alerts`);
  return handleResponse(res);
}

export async function getRuns(datasetId) {
  const res = await fetch(`${API_URL}/datasets/${datasetId}/runs`);
  return handleResponse(res);
}

export async function getDatasetStatus(id) {
  const res = await fetch(`${API_URL}/datasets/${id}/status`);
  return handleResponse(res);
}

export async function getDatasetSummary(id) {
  const res = await fetch(`${API_URL}/datasets/${id}/summary`);
  return handleResponse(res);
}
