export const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function postJSON<T>(path: string, body: any): Promise<T> {
	const r = await fetch(`${API}${path}`, {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify(body),
	});
	if (!r.ok) throw new Error(await r.text());
	return r.json();
}
