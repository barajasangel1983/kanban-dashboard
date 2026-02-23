from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import aiosqlite

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "kanban.db")

app = FastAPI(title="Kanban API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Board(BaseModel):
    id: int
    name: str


class Column(BaseModel):
    id: int
    board_id: int
    name: str
    position: int


class Card(BaseModel):
    id: int
    board_id: int
    column_id: int
    title: str
    description: Optional[str] = None
    position: int


async def init_db():
    os.makedirs(os.path.join(os.path.dirname(__file__), "..", "data"), exist_ok=True)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(
            """
            CREATE TABLE IF NOT EXISTS boards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS columns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                board_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                position INTEGER NOT NULL,
                FOREIGN KEY (board_id) REFERENCES boards(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                board_id INTEGER NOT NULL,
                column_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                position INTEGER NOT NULL,
                FOREIGN KEY (board_id) REFERENCES boards(id) ON DELETE CASCADE,
                FOREIGN KEY (column_id) REFERENCES columns(id) ON DELETE CASCADE
            );
            """
        )

        # Ensure default board + columns exist
        cursor = await db.execute("SELECT id FROM boards LIMIT 1")
        row = await cursor.fetchone()
        if row is None:
            # Create default board
            cursor = await db.execute("INSERT INTO boards (name) VALUES (?)", ("Default Board",))
            await db.commit()
            board_id = cursor.lastrowid
        else:
            board_id = row[0]

        # Ensure default columns exist
        cursor = await db.execute("SELECT COUNT(*) FROM columns WHERE board_id = ?", (board_id,))
        count = (await cursor.fetchone())[0]
        if count == 0:
            default_columns = [
                "Parking Lot",
                "Defined",
                "In Progress",
                "Blocked",
                "Done",
            ]
            for pos, name in enumerate(default_columns):
                await db.execute(
                    "INSERT INTO columns (board_id, name, position) VALUES (?, ?, ?)",
                    (board_id, name, pos),
                )
            await db.commit()


@app.on_event("startup")
async def on_startup():
    await init_db()


@app.get("/boards", response_model=List[Board])
async def list_boards():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT id, name FROM boards ORDER BY id")
        rows = await cursor.fetchall()
        return [Board(**dict(row)) for row in rows]


@app.get("/boards/{board_id}/columns", response_model=List[Column])
async def list_columns(board_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT id, board_id, name, position FROM columns WHERE board_id = ? ORDER BY position",
            (board_id,),
        )
        rows = await cursor.fetchall()
        return [Column(**dict(row)) for row in rows]


@app.get("/boards/{board_id}/cards", response_model=List[Card])
async def list_cards(board_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT id, board_id, column_id, title, description, position FROM cards WHERE board_id = ? ORDER BY column_id, position",
            (board_id,),
        )
        rows = await cursor.fetchall()
        return [Card(**dict(row)) for row in rows]


class CardCreate(BaseModel):
    board_id: int
    column_id: int
    title: str
    description: Optional[str] = None


@app.post("/cards", response_model=Card)
async def create_card(payload: CardCreate):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        # Determine next position within the column
        cursor = await db.execute(
            "SELECT COALESCE(MAX(position), -1) + 1 FROM cards WHERE board_id = ? AND column_id = ?",
            (payload.board_id, payload.column_id),
        )
        position = (await cursor.fetchone())[0]

        await db.execute(
            "INSERT INTO cards (board_id, column_id, title, description, position) VALUES (?, ?, ?, ?, ?)",
            (payload.board_id, payload.column_id, payload.title, payload.description, position),
        )
        await db.commit()

        cursor = await db.execute(
            "SELECT id, board_id, column_id, title, description, position FROM cards WHERE board_id = ? AND column_id = ? AND position = ?",
            (payload.board_id, payload.column_id, position),
        )
        row = await cursor.fetchone()
        return Card(**dict(row))


class CardMove(BaseModel):
    board_id: int
    from_column_id: int
    to_column_id: int
    new_position: int


@app.post("/cards/{card_id}/move", response_model=Card)
async def move_card(card_id: int, payload: CardMove):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        # Ensure card exists
        cursor = await db.execute(
            "SELECT id, board_id, column_id, title, description, position FROM cards WHERE id = ?",
            (card_id,),
        )
        card_row = await cursor.fetchone()
        if card_row is None:
            raise HTTPException(status_code=404, detail="Card not found")

        # Shift positions in target column
        await db.execute(
            "UPDATE cards SET position = position + 1 WHERE board_id = ? AND column_id = ? AND position >= ?",
            (payload.board_id, payload.to_column_id, payload.new_position),
        )

        # Move card
        await db.execute(
            "UPDATE cards SET column_id = ?, position = ? WHERE id = ?",
            (payload.to_column_id, payload.new_position, card_id),
        )
        await db.commit()

        cursor = await db.execute(
            "SELECT id, board_id, column_id, title, description, position FROM cards WHERE id = ?",
            (card_id,),
        )
        row = await cursor.fetchone()
        return Card(**dict(row))
