const API_URL = "http://localhost:8000";

export async function getDatasets() {
  const res = await fetch(`${API_URL}/datasets`);
  return res.json();
}

export async function createDataset(data) {
  const res = await fetch(
    `${API_URL}/datasets?name=${data.name}&description=${data.description}`,
    {
      method: "POST",
    },
  );
  return res.json();
}

export async function getAlerts(datasetId) {
  const res = await fetch(`${API_URL}/datasets/${datasetId}/alerts`);
  return res.json();
}

export async function getRuns(datasetId) {
  const res = await fetch(`http://localhost:8000/datasets/${datasetId}/runs`);
  return res.json();
}

export async function getDatasetStatus(id) {
  const res = await fetch(`http://localhost:8000/datasets/${id}/status`);
  return await res.json();
}
