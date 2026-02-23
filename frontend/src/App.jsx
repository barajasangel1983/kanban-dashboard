import { useEffect, useState } from "react";
import {
  fetchBoards,
  fetchColumns,
  fetchCards,
  createCard,
} from "./api";
import "./App.css";

function App() {
  const [boards, setBoards] = useState([]);
  const [selectedBoardId, setSelectedBoardId] = useState(null);
  const [columns, setColumns] = useState([]);
  const [cards, setCards] = useState([]);
  const [newCardTitle, setNewCardTitle] = useState("");

  // Load boards on mount
  useEffect(() => {
    fetchBoards()
      .then((data) => {
        setBoards(data);
        if (data.length > 0) {
          setSelectedBoardId(data[0].id);
        }
      })
      .catch((err) => console.error(err));
  }, []);

  // Load columns + cards when board changes
  useEffect(() => {
    if (!selectedBoardId) return;
    fetchColumns(selectedBoardId)
      .then(setColumns)
      .catch((err) => console.error(err));
    fetchCards(selectedBoardId)
      .then(setCards)
      .catch((err) => console.error(err));
  }, [selectedBoardId]);

  const handleAddCard = async () => {
    if (!newCardTitle.trim()) return;
    if (!selectedBoardId) return;

    // Add to first column (Parking Lot) by default
    const firstColumn = columns[0];
    if (!firstColumn) return;

    try {
      const card = await createCard(selectedBoardId, firstColumn.id, newCardTitle.trim());
      setCards((prev) => [...prev, card]);
      setNewCardTitle("");
    } catch (err) {
      console.error(err);
    }
  };

  const cardsByColumn = columns.reduce((acc, col) => {
    acc[col.id] = cards.filter((c) => c.column_id === col.id).sort((a, b) => a.position - b.position);
    return acc;
  }, {});

  return (
    <div className="App">
      <header className="App-header">
        <h1>Kanban Board</h1>
        {boards.length > 0 && (
          <select
            value={selectedBoardId ?? ""}
            onChange={(e) => setSelectedBoardId(Number(e.target.value))}
          >
            {boards.map((b) => (
              <option key={b.id} value={b.id}>
                {b.name}
              </option>
            ))}
          </select>
        )}
      </header>

      <section className="controls">
        <input
          type="text"
          placeholder="New card title (Parking Lot)"
          value={newCardTitle}
          onChange={(e) => setNewCardTitle(e.target.value)}
        />
        <button onClick={handleAddCard}>Add Card</button>
      </section>

      <main className="board">
        {columns.map((col) => (
          <div key={col.id} className="column">
            <h2>{col.name}</h2>
            <div className="cards">
              {(cardsByColumn[col.id] || []).map((card) => (
                <div key={card.id} className="card">
                  <strong>{card.title}</strong>
                  {card.description && <p>{card.description}</p>}
                </div>
              ))}
            </div>
          </div>
        ))}
      </main>
    </div>
  );
}

export default App;
