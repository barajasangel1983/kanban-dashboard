const API_BASE = "http://127.0.0.1:8000";

export type Board = { id: number; name: string };
export type Column = { id: number; board_id: number; name: string; position: number };
export type Card = { id: number; board_id: number; column_id: number; title: string; description?: string | null; position: number };

export async function fetchBoards(): Promise<Board[]> {
  const res = await fetch(`${API_BASE}/boards`);
  if (!res.ok) throw new Error("Failed to fetch boards");
  return res.json();
}

export async function fetchColumns(boardId: number): Promise<Column[]> {
  const res = await fetch(`${API_BASE}/boards/${boardId}/columns`);
  if (!res.ok) throw new Error("Failed to fetch columns");
  return res.json();
}

export async function fetchCards(boardId: number): Promise<Card[]> {
  const res = await fetch(`${API_BASE}/boards/${boardId}/cards`);
  if (!res.ok) throw new Error("Failed to fetch cards");
  return res.json();
}

export async function createCard(boardId: number, columnId: number, title: string, description?: string) {
  const res = await fetch(`${API_BASE}/cards`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ board_id: boardId, column_id: columnId, title, description }),
  });
  if (!res.ok) throw new Error("Failed to create card");
  return res.json();
}

export async function moveCard(cardId: number, boardId: number, fromColumnId: number, toColumnId: number, newPosition: number) {
  const res = await fetch(`${API_BASE}/cards/${cardId}/move`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ board_id: boardId, from_column_id: fromColumnId, to_column_id: toColumnId, new_position: newPosition }),
  });
  if (!res.ok) throw new Error("Failed to move card");
  return res.json();
}
