// In dev, use the Vite proxy (/api → backend) so uploads work when the app is
// opened via port forwarding or a non-localhost URL. Override with VITE_API_URL.
const API_URL =
  import.meta.env.VITE_API_URL ||
  (import.meta.env.DEV ? "/api" : "http://localhost:8000");

class ApiError extends Error {
  constructor(message, { network = false } = {}) {
    super(message);
    this.name = "ApiError";
    this.network = network;
  }
}

async function handleResponse(res) {
  if (!res.ok) {
    let detail = `Request failed with status ${res.status}`;
    try {
      const body = await res.json();
      if (body && body.detail) {
        detail =
          typeof body.detail === "string"
            ? body.detail
            : JSON.stringify(body.detail);
      }
    } catch {
      // ignore parse errors, fall back to default message
    }
    throw new ApiError(detail);
  }
  return res.json();
}

async function apiFetch(path, options = {}) {
  try {
    const res = await fetch(`${API_URL}${path}`, options);
    return handleResponse(res);
  } catch (err) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(
      "Could not reach the API server. Make sure the backend is running (port 8000) and restart the frontend dev server if you just changed settings.",
      { network: true },
    );
  }
}

export async function getDatasets() {
  return apiFetch("/datasets");
}

export async function createDataset(data) {
  const params = new URLSearchParams({ name: data.name });
  if (data.description) params.append("description", data.description);
  return apiFetch(`/datasets?${params.toString()}`, { method: "POST" });
}

export async function uploadDataset(datasetId, file) {
  const formData = new FormData();
  formData.append("file", file);
  return apiFetch(`/datasets/${datasetId}/upload`, {
    method: "POST",
    body: formData,
  });
}

export async function getAlerts(datasetId) {
  return apiFetch(`/datasets/${datasetId}/alerts`);
}

export async function getRuns(datasetId) {
  return apiFetch(`/datasets/${datasetId}/runs`);
}

export async function getDatasetStatus(id) {
  return apiFetch(`/datasets/${id}/status`);
}

export async function getDatasetSummary(id) {
  return apiFetch(`/datasets/${id}/summary`);
}
