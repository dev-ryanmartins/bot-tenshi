"""
Módulo de persistência de infrações com aiosqlite.
Gerencia avisos, banimentos e silenciamentos vinculados a usuários.
"""

import os
from datetime import UTC, datetime
from typing import List, Optional

import aiosqlite

DB_PATH = os.environ.get("TENSHI_DB_PATH", "data/tenshi.db")


class Database:
    """Camada assíncrona simples para notas e avisos de moderação."""

    def __init__(self, path: str = DB_PATH):
        self.path = path

    async def initialize(self) -> None:
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        async with aiosqlite.connect(self.path) as db:
            await db.executescript("""
                CREATE TABLE IF NOT EXISTS notas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    texto TEXT NOT NULL,
                    moderator_id INTEGER,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS avisos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    texto TEXT NOT NULL,
                    moderator_id INTEGER,
                    created_at TEXT NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1
                );
                CREATE INDEX IF NOT EXISTS idx_notas_user_id ON notas(user_id);
                CREATE INDEX IF NOT EXISTS idx_avisos_user_id ON avisos(user_id);
            """)
            await db.commit()

    async def add_note(self, user_id: int, texto: str, moderator_id: int | None = None) -> int:
        await self.initialize()
        created_at = datetime.now(UTC).replace(tzinfo=None).isoformat()
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                "INSERT INTO notas (user_id, texto, moderator_id, created_at) VALUES (?, ?, ?, ?)",
                (user_id, texto, moderator_id, created_at),
            )
            await db.commit()
            return int(cursor.lastrowid)

    async def get_notes(self, user_id: int) -> List[dict]:
        await self.initialize()
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM notas WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
            )
            return [dict(row) for row in await cursor.fetchall()]

    async def add_warning(self, user_id: int, texto: str, moderator_id: int | None = None) -> int:
        await self.initialize()
        created_at = datetime.now(UTC).replace(tzinfo=None).isoformat()
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                "INSERT INTO avisos (user_id, texto, moderator_id, created_at) VALUES (?, ?, ?, ?)",
                (user_id, texto, moderator_id, created_at),
            )
            await db.commit()
            return int(cursor.lastrowid)

    async def get_warnings(self, user_id: int, active_only: bool = True) -> List[dict]:
        await self.initialize()
        query = "SELECT * FROM avisos WHERE user_id = ?"
        if active_only:
            query += " AND is_active = 1"
        query += " ORDER BY created_at DESC"
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(query, (user_id,))
            return [dict(row) for row in await cursor.fetchall()]


database = Database()


async def _init_db():
    """Inicializa o banco de dados com as tabelas necessárias."""
    await database.initialize()
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS infractions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                infraction_type TEXT NOT NULL,
                reason TEXT,
                moderator_id INTEGER,
                created_at TEXT NOT NULL,
                expires_at TEXT,
                is_active INTEGER DEFAULT 1
            )
        """)
        
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_id ON infractions(user_id)
        """)
        
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_infraction_type ON infractions(infraction_type)
        """)
        
        await db.commit()


async def _ensure_db():
    """Garante que o banco existe antes de usar."""
    await _init_db()


async def register_infraction(
    user_id: int,
    infraction_type: str,
    reason: str = "",
    moderator_id: Optional[int] = None,
    expires_at: Optional[str] = None
) -> int:
    """
    Registra uma nova infração no banco de dados.
    
    Parâmetros:
        user_id: ID do usuário que sofre a infração
        infraction_type: tipo de infração (aviso, mute, ban)
        reason: motivo da infração
        moderator_id: ID do moderador (opcional)
        expires_at: data de expiração em ISO format (opcional)
    
    Retorna:
        ID da infração registrada
    """
    await _ensure_db()
    
    created_at = datetime.now(UTC).replace(tzinfo=None).isoformat()
    
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            INSERT INTO infractions (user_id, infraction_type, reason, moderator_id, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, infraction_type, reason, moderator_id, created_at, expires_at)
        )
        await db.commit()
        infraction_id = int(cursor.lastrowid)

    if infraction_type in {"aviso", "warn", "warn_manual"}:
        await database.add_warning(user_id, reason or "Sem motivo especificado", moderator_id)
    return infraction_id


async def get_user_infractions(user_id: int, active_only: bool = True) -> List[dict]:
    """
    Recupera todas as infrações de um usuário.
    
    Parâmetros:
        user_id: ID do usuário
        active_only: se True, retorna apenas infrações ativas
    
    Retorna:
        Lista de dicts com as infrações
    """
    await _ensure_db()
    
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        if active_only:
            cursor = await db.execute(
                """
                SELECT * FROM infractions 
                WHERE user_id = ? AND is_active = 1
                ORDER BY created_at DESC
                """,
                (user_id,)
            )
        else:
            cursor = await db.execute(
                """
                SELECT * FROM infractions 
                WHERE user_id = ?
                ORDER BY created_at DESC
                """,
                (user_id,)
            )
        
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def count_active_infractions(user_id: int, infraction_type: Optional[str] = None) -> int:
    """
    Conta o número de infrações ativas de um usuário.
    
    Parâmetros:
        user_id: ID do usuário
        infraction_type: filtrar por tipo de infração (opcional)
    
    Retorna:
        Número de infrações ativas
    """
    await _ensure_db()
    
    async with aiosqlite.connect(DB_PATH) as db:
        if infraction_type:
            cursor = await db.execute(
                """
                SELECT COUNT(*) as count FROM infractions 
                WHERE user_id = ? AND is_active = 1 AND infraction_type = ?
                """,
                (user_id, infraction_type)
            )
        else:
            cursor = await db.execute(
                """
                SELECT COUNT(*) as count FROM infractions 
                WHERE user_id = ? AND is_active = 1
                """,
                (user_id,)
            )
        
        result = await cursor.fetchone()
        return result[0] if result else 0


async def deactivate_infraction(infraction_id: int):
    """
    Desativa uma infração existente (marca como inativa).
    
    Parâmetros:
        infraction_id: ID da infração a desativar
    """
    await _ensure_db()
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            UPDATE infractions SET is_active = 0 WHERE id = ?
            """,
            (infraction_id,)
        )
        await db.commit()


async def get_user_warning_count(user_id: int) -> int:
    """Retorna o número de avisos ativos de um usuário."""
    return await count_active_infractions(user_id, "aviso")


async def get_user_mute_count(user_id: int) -> int:
    """Retorna o número de mutas ativas de um usuário."""
    return await count_active_infractions(user_id, "mute")


async def get_user_ban_count(user_id: int) -> int:
    """Retorna o número de bans ativos de um usuário."""
    return await count_active_infractions(user_id, "ban")


async def clear_expired_infractions():
    """Remove infrações expiradas do banco de dados."""
    await _ensure_db()
    
    now = datetime.now(UTC).replace(tzinfo=None).isoformat()
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            UPDATE infractions SET is_active = 0
            WHERE expires_at IS NOT NULL AND expires_at < ? AND is_active = 1
            """,
            (now,)
        )
        await db.commit()


async def get_infractions_summary(user_id: int) -> dict:
    """
    Retorna um resumo das infrações de um usuário.
    
    Retorna:
        Dict com contagem de avisos, mutes e bans ativos
    """
    warnings = await count_active_infractions(user_id, "aviso")
    mutes = await count_active_infractions(user_id, "mute")
    bans = await count_active_infractions(user_id, "ban")
    
    return {
        "avisos": warnings,
        "mutes": mutes,
        "bans": bans,
        "total": warnings + mutes + bans
    }
