const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/chat";

// ------------------- API -------------------
export async function sendMessageAPI(
  message: string,
  latitude?: number,
  longitude?: number
) {
  const payload: any = { prompt: message };
  if (latitude !== undefined) payload.latitude = latitude;
  if (longitude !== undefined) payload.longitude = longitude;

  const res = await fetch(API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) throw new Error("API error");
  return res.json();
}