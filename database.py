import sqlite3
import os
from datetime import datetime

DB_PATH = os.environ.get("DB_PATH", "gastos.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS gastos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                monto_total INTEGER NOT NULL,
                descripcion TEXT NOT NULL,
                categoria TEXT NOT NULL,
                tarjeta TEXT NOT NULL DEFAULT 'crédito',
                tipo TEXT NOT NULL DEFAULT 'personal',  -- 'personal' | 'split' | 'adelanto'
                fecha TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS deudas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gasto_id INTEGER NOT NULL REFERENCES gastos(id),
                persona TEXT NOT NULL,
                monto INTEGER NOT NULL,
                pagado INTEGER NOT NULL DEFAULT 0,
                fecha_pago TEXT
            );
        """)
        conn.commit()
    print("Base de datos lista.")


def insertar_gasto_personal(user_id, monto, descripcion, categoria, tarjeta):
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO gastos (user_id, monto_total, descripcion, categoria, tarjeta, tipo, fecha) VALUES (?,?,?,?,?,?,?)",
            (user_id, monto, descripcion, categoria, tarjeta, "personal", fecha),
        )
        conn.commit()


def insertar_gasto_split(user_id, monto_total, descripcion, categoria, tarjeta, partes):
    """
    partes: list of (persona, monto)
    Si persona es None = es la parte del propio usuario
    """
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO gastos (user_id, monto_total, descripcion, categoria, tarjeta, tipo, fecha) VALUES (?,?,?,?,?,?,?)",
            (user_id, monto_total, descripcion, categoria, tarjeta, "split", fecha),
        )
        gasto_id = cur.lastrowid
        for persona, monto in partes:
            if persona is not None:
                conn.execute(
                    "INSERT INTO deudas (gasto_id, persona, monto) VALUES (?,?,?)",
                    (gasto_id, persona.lower().strip(), monto),
                )
        conn.commit()
    return gasto_id


def insertar_adelanto(user_id, monto_total, descripcion, categoria, tarjeta, persona):
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO gastos (user_id, monto_total, descripcion, categoria, tarjeta, tipo, fecha) VALUES (?,?,?,?,?,?,?)",
            (user_id, monto_total, descripcion, categoria, tarjeta, "adelanto", fecha),
        )
        gasto_id = cur.lastrowid
        conn.execute(
            "INSERT INTO deudas (gasto_id, persona, monto) VALUES (?,?,?)",
            (gasto_id, persona.lower().strip(), monto_total),
        )
        conn.commit()
    return gasto_id


def registrar_pago(user_id, persona, monto=None):
    """Marca deudas como pagadas. Si monto=None, paga todo."""
    persona = persona.lower().strip()
    fecha_pago = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_conn() as conn:
        # Obtener deudas pendientes de esa persona para este user
        rows = conn.execute("""
            SELECT d.id, d.monto FROM deudas d
            JOIN gastos g ON d.gasto_id = g.id
            WHERE g.user_id=? AND d.persona=? AND d.pagado=0
            ORDER BY d.id ASC
        """, (user_id, persona)).fetchall()

        if not rows:
            return 0

        if monto is None:
            # Pagar todo
            ids = [r["id"] for r in rows]
            conn.execute(
                f"UPDATE deudas SET pagado=1, fecha_pago=? WHERE id IN ({','.join('?'*len(ids))})",
                [fecha_pago] + ids,
            )
            total = sum(r["monto"] for r in rows)
        else:
            # Pagar parcial
            total = 0
            restante = monto
            for row in rows:
                if restante <= 0:
                    break
                if row["monto"] <= restante:
                    conn.execute("UPDATE deudas SET pagado=1, fecha_pago=? WHERE id=?", (fecha_pago, row["id"]))
                    restante -= row["monto"]
                    total += row["monto"]
                else:
                    # Pago parcial de esta deuda — dividir en dos
                    conn.execute("UPDATE deudas SET monto=? WHERE id=?", (row["monto"] - restante, row["id"]))
                    conn.execute(
                        "INSERT INTO deudas (gasto_id, persona, monto, pagado, fecha_pago) VALUES (?,?,?,1,?)",
                        (row["gasto_id"], persona, restante, fecha_pago),
                    )
                    total += restante
                    restante = 0
        conn.commit()
        return total


def obtener_deudas_por_persona(user_id):
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT d.persona, SUM(d.monto) as total
            FROM deudas d
            JOIN gastos g ON d.gasto_id = g.id
            WHERE g.user_id=? AND d.pagado=0
            GROUP BY d.persona
            ORDER BY total DESC
        """, (user_id,)).fetchall()
    return rows


def obtener_deuda_persona(user_id, persona):
    persona = persona.lower().strip()
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT d.monto, g.descripcion, g.fecha
            FROM deudas d
            JOIN gastos g ON d.gasto_id = g.id
            WHERE g.user_id=? AND d.persona=? AND d.pagado=0
            ORDER BY g.fecha DESC
        """, (user_id, persona)).fetchall()
    return rows


def obtener_gastos_mes(user_id, anio, mes):
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT id, monto_total, descripcion, categoria, tarjeta, tipo, fecha
            FROM gastos
            WHERE user_id=? AND strftime('%Y',fecha)=? AND strftime('%m',fecha)=?
            ORDER BY fecha DESC
        """, (user_id, str(anio), f"{mes:02d}")).fetchall()
    return rows


def obtener_gastos_categoria(user_id, categoria, anio, mes):
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT monto_total, descripcion, tipo, tarjeta, fecha
            FROM gastos
            WHERE user_id=? AND lower(categoria)=lower(?)
              AND strftime('%Y',fecha)=? AND strftime('%m',fecha)=?
            ORDER BY fecha DESC
        """, (user_id, categoria, str(anio), f"{mes:02d}")).fetchall()
    return rows


def obtener_ultimos_gastos(user_id, limite=10):
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT monto_total, descripcion, categoria, tipo, tarjeta, fecha
            FROM gastos WHERE user_id=?
            ORDER BY fecha DESC LIMIT ?
        """, (user_id, limite)).fetchall()
    return rows


def obtener_gastos_multiples_meses(user_id, meses):
    """meses: list of (anio, mes)"""
    resultados = {}
    with get_conn() as conn:
        for anio, mes in meses:
            rows = conn.execute("""
                SELECT monto_total, categoria, tipo FROM gastos
                WHERE user_id=? AND strftime('%Y',fecha)=? AND strftime('%m',fecha)=?
            """, (user_id, str(anio), f"{mes:02d}")).fetchall()
            resultados[(anio, mes)] = rows
    return resultados
