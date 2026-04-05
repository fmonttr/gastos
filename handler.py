from datetime import datetime
from ai import parse_mensaje
from database import (
    insertar_gasto_personal,
    insertar_gasto_split,
    insertar_adelanto,
    registrar_pago,
)
from queries import (
    resumen_mes,
    resumen_categoria,
    ultimos_gastos,
    deudas_todas,
    deuda_persona,
    comparar_meses,
    metricas,
    fmt,
)


async def handle(texto: str, user_id: int) -> str:
    now = datetime.now()
    mes = now.month
    anio = now.year

    try:
        parsed = await parse_mensaje(texto)
    except Exception as e:
        return "❓ No entendí bien. Intenta de nuevo o escribe *ayuda*."

    accion = parsed.get("accion")
    datos = parsed.get("datos", {})

    # ── REGISTRAR GASTO ──────────────────────────────────────────────
    if accion == "registrar_gasto":
        monto = datos.get("monto_total", 0)
        desc = datos.get("descripcion", "gasto")
        cat = datos.get("categoria", "Otro")
        tarjeta = datos.get("tarjeta", "crédito")
        tipo = datos.get("tipo", "personal")
        partes = datos.get("partes", [])

        emoji_t = "💳" if tarjeta == "crédito" else "🏦"
        emoji_c = cat_emoji_simple(cat)

        if tipo == "personal":
            insertar_gasto_personal(user_id, monto, desc, cat, tarjeta)
            return (
                f"✅ *{desc.capitalize()}* — {fmt(monto)}\n"
                f"{emoji_c} {cat}  {emoji_t} {tarjeta.capitalize()}"
            )

        elif tipo == "split":
            partes_db = [(p["persona"], p["monto"]) for p in partes]
            insertar_gasto_split(user_id, monto, desc, cat, tarjeta, partes_db)
            otros = sum(p["monto"] for p in partes)
            tuyo = monto - otros
            lineas = [
                f"✅ *{desc.capitalize()}* — {fmt(monto)} {emoji_t}\n",
                f"👤 Tu parte: {fmt(tuyo)}",
            ]
            for p in partes:
                lineas.append(f"👥 {p['persona'].capitalize()}: {fmt(p['monto'])}")
            return "\n".join(lineas)

        elif tipo == "adelanto":
            persona = partes[0]["persona"] if partes else "?"
            insertar_adelanto(user_id, monto, desc, cat, tarjeta, persona)
            return (
                f"↗️ *Adelanto registrado*\n"
                f"{desc.capitalize()} — {fmt(monto)}\n"
                f"Le cobrarás a *{persona.capitalize()}*"
            )

    # ── CONSULTAR DEUDAS ─────────────────────────────────────────────
    elif accion == "consultar_deudas":
        persona = datos.get("persona")
        if persona:
            return deuda_persona(user_id, persona)
        return deudas_todas(user_id)

    # ── REGISTRAR PAGO ───────────────────────────────────────────────
    elif accion == "registrar_pago":
        persona = datos.get("persona", "")
        monto = datos.get("monto")
        total_pagado = registrar_pago(user_id, persona, monto)
        if total_pagado == 0:
            return f"⚠️ No encontré deudas pendientes de *{persona.capitalize()}*."
        return f"✅ Registré que *{persona.capitalize()}* te pagó {fmt(total_pagado)}."

    # ── RESUMEN MES ──────────────────────────────────────────────────
    elif accion == "consultar_mes":
        return resumen_mes(user_id, anio, mes)

    # ── POR CATEGORÍA ────────────────────────────────────────────────
    elif accion == "consultar_categoria":
        cat = datos.get("categoria", "Otro")
        return resumen_categoria(user_id, cat, anio, mes)

    # ── ÚLTIMOS GASTOS ───────────────────────────────────────────────
    elif accion == "ultimos_gastos":
        return ultimos_gastos(user_id)

    # ── COMPARAR MESES ───────────────────────────────────────────────
    elif accion == "comparar_meses":
        return comparar_meses(user_id)

    # ── MÉTRICAS ─────────────────────────────────────────────────────
    elif accion == "metricas":
        return metricas(user_id)

    # ── DESCONOCIDO ──────────────────────────────────────────────────
    else:
        return (
            "👋 Puedo ayudarte con:\n\n"
            "*Registrar gastos:*\n"
            "• `5000 oxxo`\n"
            "• `10000 falabella débito`\n"
            "• `23000 mcdonalds, tomás y flo`\n"
            "• `15000 doctor, mamá` _(adelanto)_\n\n"
            "*Consultas:*\n"
            "• `¿cuánto gasté este mes?`\n"
            "• `¿cuánto me deben?`\n"
            "• `tomás me pagó`\n"
            "• `últimos gastos`\n"
            "• `métricas`\n"
            "• `compara meses`"
        )


def cat_emoji_simple(cat: str) -> str:
    return {
        "Comida": "🍽️", "Transporte": "🚗", "Salud": "💊",
        "Entretenimiento": "🎬", "Hogar": "🏠", "Ropa": "👕",
        "Tecnología": "💻", "Educación": "📚", "Suscripciones": "📱", "Otro": "📦",
    }.get(cat, "📦")
