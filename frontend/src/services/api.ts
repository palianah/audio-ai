const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function uploadAudio(file: File): Promise<Response> {
  const formData = new FormData();
  formData.append("file", file);
  return fetch(`${API_BASE}/api/upload`, { method: "POST", body: formData });
}

export async function requestSeparation(fileId: string, stems?: string[]): Promise<Response> {
  return fetch(`${API_BASE}/api/separate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ file_id: fileId, stems }),
  });
}

export async function getTaskStatus(taskId: string): Promise<Response> {
  return fetch(`${API_BASE}/api/tasks/${taskId}`);
}

export async function applyEffects(fileId: string, effects: unknown[]): Promise<Response> {
  return fetch(`${API_BASE}/api/effects`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ file_id: fileId, effects }),
  });
}

export async function requestTranscription(fileId: string): Promise<Response> {
  return fetch(`${API_BASE}/api/transcribe`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ file_id: fileId }),
  });
}
