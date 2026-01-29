"""Database module for storing betting records in SQLite."""

import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import List, Optional


class BettingDatabase:
    """Manages SQLite database for betting records."""

    def __init__(self, db_path: str = "/home/marcos/projetos/bet/data/betting.db"):
        """
        Initialize database connection.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._create_table()

    def _create_table(self):
        """Create the registros table if it doesn't exist, with migration support."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Check if old table exists
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='registros'
            """)
            old_table_exists = cursor.fetchone() is not None

            if old_table_exists:
                # Check if table has old structure (observacoes column exists)
                cursor.execute("PRAGMA table_info(registros)")
                columns = [col[1] for col in cursor.fetchall()]

                # Check if migration is needed (add banca field)
                if 'banca' not in columns:
                    print("🔄 Migrando banco de dados - adicionando campo 'banca'...")

                    # Add banca column with default value 427.0
                    cursor.execute("""
                        ALTER TABLE registros ADD COLUMN banca REAL DEFAULT 427.0
                    """)

                    # Update all existing records to have banca calculated backwards
                    cursor.execute("""
                        UPDATE registros SET banca = 427.0 WHERE banca IS NULL
                    """)

                    print("✅ Migração concluída! Campo 'banca' adicionado com valor inicial 427.0.")
                    conn.commit()

                # Check if migration is needed (add stake field)
                if 'stake' not in columns:
                    print("🔄 Migrando banco de dados - adicionando campo 'stake'...")

                    # Add stake column with default value 25.0
                    cursor.execute("""
                        ALTER TABLE registros ADD COLUMN stake REAL DEFAULT 25.0
                    """)

                    # Update all existing records to have stake = 25.0
                    cursor.execute("""
                        UPDATE registros SET stake = 25.0 WHERE stake IS NULL
                    """)

                    print("✅ Migração concluída! Campo 'stake' adicionado com valor padrão 25.0.")
                    conn.commit()

                # Check if migration is needed (remove resultado field)
                if 'resultado' in columns:
                    print("🔄 Migrando banco de dados - removendo campo 'resultado'...")

                    # Create new table without resultado
                    cursor.execute("""
                        CREATE TABLE registros_new (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            data DATE NOT NULL,
                            estrategia TEXT NOT NULL DEFAULT 'Under Limite',
                            aposta TEXT NOT NULL,
                            lucro_prejuizo REAL,
                            lucro_acumulado REAL,
                            banca REAL DEFAULT 427.0,
                            stake REAL DEFAULT 25.0,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)

                    # Copy existing data (without resultado)
                    cursor.execute("""
                        INSERT INTO registros_new (id, data, estrategia, aposta, lucro_prejuizo, banca, stake, created_at)
                        SELECT id, data, estrategia, aposta, lucro_prejuizo, 427.0, 25.0, created_at
                        FROM registros
                        ORDER BY data ASC, created_at ASC
                    """)

                    # Drop old table (already have backup from previous migration)
                    cursor.execute("DROP TABLE IF EXISTS registros")

                    # Rename new table
                    cursor.execute("ALTER TABLE registros_new RENAME TO registros")

                    # Recalculate accumulated profit for all records
                    self._recalcular_lucro_acumulado_todos(conn)

                    print("✅ Migração concluída! Campo 'resultado' removido.")
                    conn.commit()
                    return

            # Create new table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS registros (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data DATE NOT NULL,
                    estrategia TEXT NOT NULL DEFAULT 'Under Limite',
                    aposta TEXT NOT NULL,
                    lucro_prejuizo REAL,
                    lucro_acumulado REAL,
                    banca REAL DEFAULT 427.0,
                    stake REAL DEFAULT 25.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def _recalcular_lucro_acumulado_todos(self, conn):
        """Recalculate accumulated profit for all records."""
        cursor = conn.cursor()

        # Get all records ordered by date and creation time
        cursor.execute("""
            SELECT id, lucro_prejuizo
            FROM registros
            ORDER BY data ASC, created_at ASC
        """)
        registros = cursor.fetchall()

        lucro_acumulado = 0.0
        for registro_id, lucro_prejuizo in registros:
            if lucro_prejuizo is not None:
                lucro_acumulado += lucro_prejuizo

            cursor.execute(
                "UPDATE registros SET lucro_acumulado = ? WHERE id = ?",
                (lucro_acumulado, registro_id),
            )

    def _calcular_lucro_acumulado(self, data_registro: date, created_at_registro: datetime, conn) -> float:
        """Calculate accumulated profit up to the given date and time."""
        cursor = conn.cursor()

        # Sum all profits up to (but not including) this record
        cursor.execute(
            """
            SELECT COALESCE(SUM(lucro_prejuizo), 0)
            FROM registros
            WHERE data < ? OR (data = ? AND created_at < ?)
        """,
            (data_registro.isoformat(), data_registro.isoformat(), created_at_registro.isoformat()),
        )
        return cursor.fetchone()[0]

    def obter_banca_atual(self) -> float:
        """
        Get the current bankroll (banca) from the most recent record.

        Returns:
            Current bankroll, or 427.0 if no records exist
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT banca, lucro_prejuizo FROM registros
                ORDER BY data DESC, created_at DESC
                LIMIT 1
            """)
            result = cursor.fetchone()
            if result:
                banca_anterior = result[0] or 427.0
                lucro = result[1] or 0.0
                return banca_anterior + lucro
            return 427.0

    def calcular_stake_da_banca(self, banca: float) -> float:
        """
        Calculate stake as 5% of the bankroll.

        Args:
            banca: Current bankroll

        Returns:
            Stake amount (5% of banca)
        """
        return round(banca * 0.05, 2)

    def obter_ultima_stake(self) -> float:
        """
        Get the stake from the most recent record.

        Returns:
            Stake from the last record, or calculated from initial banca (427.0)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT stake FROM registros
                ORDER BY data DESC, created_at DESC
                LIMIT 1
            """)
            result = cursor.fetchone()
            if result:
                return result[0]
            # No records, calculate from initial banca
            return self.calcular_stake_da_banca(427.0)

    def adicionar_registro(
        self,
        aposta: str,
        lucro_prejuizo: Optional[float] = None,
        estrategia: str = "Under Limite",
        data: Optional[date] = None,
        stake: Optional[float] = None,
    ) -> int:
        """
        Add a new betting record.

        Args:
            aposta: Description of the bet
            lucro_prejuizo: Profit or loss amount
            estrategia: Betting strategy (default: 'Under Limite')
            data: Date of the bet (defaults to today)
            stake: Stake amount (if None, calculated as 5% of current bankroll)

        Returns:
            ID of the inserted record
        """
        if data is None:
            data = date.today()

        # Calculate current bankroll
        banca_atual = self.obter_banca_atual()

        # If stake not provided, calculate from bankroll (5%)
        if stake is None:
            stake = self.calcular_stake_da_banca(banca_atual)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Insert record first to get created_at timestamp
            now = datetime.now()
            cursor.execute(
                """
                INSERT INTO registros (data, estrategia, aposta, lucro_prejuizo, banca, stake, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (data.isoformat(), estrategia, aposta, lucro_prejuizo, banca_atual, stake, now.isoformat()),
            )
            registro_id = cursor.lastrowid

            # Calculate accumulated profit up to this point using the actual created_at
            lucro_acumulado_anterior = self._calcular_lucro_acumulado(data, now, conn)
            lucro_acumulado_atual = lucro_acumulado_anterior + (lucro_prejuizo or 0)

            # Update with calculated accumulated profit
            cursor.execute(
                "UPDATE registros SET lucro_acumulado = ? WHERE id = ?",
                (lucro_acumulado_atual, registro_id),
            )

            # Recalculate accumulated profit for all subsequent records
            cursor.execute("""
                SELECT id, lucro_prejuizo
                FROM registros
                WHERE data > ? OR (data = ? AND id > ?)
                ORDER BY data ASC, created_at ASC
            """, (data.isoformat(), data.isoformat(), registro_id))

            registros_posteriores = cursor.fetchall()
            lucro_acum = lucro_acumulado_atual

            for reg_id, lucro_prej in registros_posteriores:
                if lucro_prej is not None:
                    lucro_acum += lucro_prej
                cursor.execute(
                    "UPDATE registros SET lucro_acumulado = ? WHERE id = ?",
                    (lucro_acum, reg_id),
                )

            conn.commit()
            return registro_id

    def buscar_registros(
        self,
        data_inicio: Optional[date] = None,
        data_fim: Optional[date] = None,
        estrategia: Optional[str] = None,
    ) -> List[dict]:
        """
        Search for betting records with filters.

        Args:
            data_inicio: Start date filter
            data_fim: End date filter
            estrategia: Filter by strategy

        Returns:
            List of records as dictionaries
        """
        query = "SELECT * FROM registros WHERE 1=1"
        params = []

        if data_inicio:
            query += " AND data >= ?"
            params.append(data_inicio.isoformat())

        if data_fim:
            query += " AND data <= ?"
            params.append(data_fim.isoformat())

        if estrategia:
            query += " AND estrategia = ?"
            params.append(estrategia)

        query += " ORDER BY data DESC, created_at DESC"

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

        return [dict(row) for row in rows]

    def buscar_por_periodo(self, periodo: str) -> List[dict]:
        """
        Search records by predefined period.

        Args:
            periodo: Period type ('hoje', 'semana', 'mes', 'ultimos_7_dias', 'ultimos_30_dias')

        Returns:
            List of records as dictionaries
        """
        hoje = date.today()

        if periodo == "hoje":
            return self.buscar_registros(data_inicio=hoje, data_fim=hoje)

        elif periodo == "semana":
            # Start of current week (Monday)
            inicio_semana = hoje - timedelta(days=hoje.weekday())
            return self.buscar_registros(data_inicio=inicio_semana, data_fim=hoje)

        elif periodo == "mes":
            # Start of current month
            inicio_mes = hoje.replace(day=1)
            return self.buscar_registros(data_inicio=inicio_mes, data_fim=hoje)

        elif periodo == "ultimos_7_dias":
            data_inicio = hoje - timedelta(days=7)
            return self.buscar_registros(data_inicio=data_inicio, data_fim=hoje)

        elif periodo == "ultimos_30_dias":
            data_inicio = hoje - timedelta(days=30)
            return self.buscar_registros(data_inicio=data_inicio, data_fim=hoje)

        else:
            raise ValueError(f"Período inválido: {periodo}")

    def calcular_estatisticas(self, registros: List[dict]) -> dict:
        """
        Calculate statistics from a list of records.

        Args:
            registros: List of betting records

        Returns:
            Dictionary with statistics
        """
        if not registros:
            return {
                "total": 0,
                "lucro_total": 0.0,
                "lucro_medio": 0.0,
            }

        total = len(registros)

        # Calculate profit/loss
        lucro_total = sum(
            r["lucro_prejuizo"] for r in registros if r["lucro_prejuizo"] is not None
        )
        registros_com_lucro = [r for r in registros if r["lucro_prejuizo"] is not None]
        lucro_medio = lucro_total / len(registros_com_lucro) if registros_com_lucro else 0.0

        return {
            "total": total,
            "lucro_total": lucro_total,
            "lucro_medio": lucro_medio,
        }

    def deletar_registro(self, registro_id: int) -> bool:
        """
        Delete a record by ID.

        Args:
            registro_id: ID of the record to delete

        Returns:
            True if deleted, False if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM registros WHERE id = ?", (registro_id,))
            conn.commit()
            return cursor.rowcount > 0

    def atualizar_registro(
        self,
        registro_id: int,
        aposta: Optional[str] = None,
        lucro_prejuizo: Optional[float] = None,
        estrategia: Optional[str] = None,
    ) -> bool:
        """
        Update an existing record.

        Args:
            registro_id: ID of the record to update
            aposta: New bet description
            lucro_prejuizo: New profit/loss value
            estrategia: New strategy

        Returns:
            True if updated, False if not found
        """
        updates = []
        params = []

        if aposta is not None:
            updates.append("aposta = ?")
            params.append(aposta)

        if lucro_prejuizo is not None:
            updates.append("lucro_prejuizo = ?")
            params.append(lucro_prejuizo)

        if estrategia is not None:
            updates.append("estrategia = ?")
            params.append(estrategia)

        if not updates:
            return False

        params.append(registro_id)
        query = f"UPDATE registros SET {', '.join(updates)} WHERE id = ?"

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()

            # If lucro_prejuizo was updated, recalculate all accumulated profits
            if lucro_prejuizo is not None:
                self._recalcular_lucro_acumulado_todos(conn)
                conn.commit()

            return cursor.rowcount > 0
