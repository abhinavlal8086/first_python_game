"""SQLite persistence for save slots, missions, and achievements."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import sqlite3
from typing import Iterable


@dataclass
class SaveSlot:
    id: int
    name: str
    score: int
    lives: int
    level: int
    mission_unlocked: int
    current_streak: int
    max_streak: int
    total_kills: int
    updated_at: str


class GameDatabase:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS save_slots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    score INTEGER NOT NULL DEFAULT 0,
                    lives INTEGER NOT NULL DEFAULT 3,
                    level INTEGER NOT NULL DEFAULT 1,
                    mission_unlocked INTEGER NOT NULL DEFAULT 1,
                    current_streak INTEGER NOT NULL DEFAULT 0,
                    max_streak INTEGER NOT NULL DEFAULT 0,
                    total_kills INTEGER NOT NULL DEFAULT 0,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS achievements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    save_id INTEGER NOT NULL,
                    achievement_key TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    unlocked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(save_id, achievement_key),
                    FOREIGN KEY(save_id) REFERENCES save_slots(id) ON DELETE CASCADE
                );
                """
            )

    def list_slots(self) -> list[SaveSlot]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, name, score, lives, level, mission_unlocked,
                       current_streak, max_streak, total_kills, updated_at
                FROM save_slots
                ORDER BY updated_at DESC, id DESC
                """
            ).fetchall()
        return [self._row_to_slot(row) for row in rows]

    def create_slot(self, name: str) -> SaveSlot:
        now = datetime.utcnow().isoformat(timespec="seconds")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO save_slots(name, updated_at)
                VALUES(?, ?)
                """,
                (name, now),
            )
            row = conn.execute(
                """
                SELECT id, name, score, lives, level, mission_unlocked,
                       current_streak, max_streak, total_kills, updated_at
                FROM save_slots
                WHERE id = last_insert_rowid()
                """
            ).fetchone()
        if row is None:
            raise RuntimeError("Failed to create save slot")
        return self._row_to_slot(row)

    def delete_slot(self, slot_id: int) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM save_slots WHERE id = ?", (slot_id,))
            conn.execute("DELETE FROM achievements WHERE save_id = ?", (slot_id,))

    def save_progress(
        self,
        slot_id: int,
        *,
        score: int,
        lives: int,
        level: int,
        mission_unlocked: int,
        current_streak: int,
        max_streak: int,
        total_kills: int,
    ) -> None:
        now = datetime.utcnow().isoformat(timespec="seconds")
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE save_slots
                SET score = ?,
                    lives = ?,
                    level = ?,
                    mission_unlocked = ?,
                    current_streak = ?,
                    max_streak = ?,
                    total_kills = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    int(score),
                    int(lives),
                    int(level),
                    int(max(1, mission_unlocked)),
                    int(current_streak),
                    int(max_streak),
                    int(total_kills),
                    now,
                    int(slot_id),
                ),
            )

    def get_slot(self, slot_id: int) -> SaveSlot | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, name, score, lives, level, mission_unlocked,
                       current_streak, max_streak, total_kills, updated_at
                FROM save_slots
                WHERE id = ?
                """,
                (slot_id,),
            ).fetchone()
        return self._row_to_slot(row) if row is not None else None

    def load_achievement_keys(self, slot_id: int) -> set[str]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT achievement_key
                FROM achievements
                WHERE save_id = ?
                """,
                (slot_id,),
            ).fetchall()
        return {str(row["achievement_key"]) for row in rows}

    def unlock_achievement(
        self,
        slot_id: int,
        key: str,
        title: str,
        description: str,
    ) -> bool:
        now = datetime.utcnow().isoformat(timespec="seconds")
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO achievements(save_id, achievement_key, title, description, unlocked_at)
                VALUES(?, ?, ?, ?, ?)
                """,
                (slot_id, key, title, description, now),
            )
            return cursor.rowcount > 0

    def list_achievements(self, slot_id: int) -> Iterable[sqlite3.Row]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT achievement_key, title, description, unlocked_at
                FROM achievements
                WHERE save_id = ?
                ORDER BY unlocked_at DESC
                """,
                (slot_id,),
            ).fetchall()
        return rows

    @staticmethod
    def _row_to_slot(row: sqlite3.Row) -> SaveSlot:
        return SaveSlot(
            id=int(row["id"]),
            name=str(row["name"]),
            score=int(row["score"]),
            lives=int(row["lives"]),
            level=int(row["level"]),
            mission_unlocked=int(row["mission_unlocked"]),
            current_streak=int(row["current_streak"]),
            max_streak=int(row["max_streak"]),
            total_kills=int(row["total_kills"]),
            updated_at=str(row["updated_at"]),
        )
