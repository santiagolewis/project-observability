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
