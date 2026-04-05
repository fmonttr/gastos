from database import (
    obtener_gastos_mes,
    obtener_gastos_categoria,
    obtener_ultimos_gastos,
    obtener_deudas_por_persona,
    obtener_deuda_persona,
    obtener_gastos_multiples_meses,
)
from datetime import datetime, date
from collections import defaultdict

MESES = ["", "enero", "febrero", "marzo", "abril", "mayo", "junio",
         "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

CAT_EMOJI = {
    "comida": "🍽️", "transporte": "🚗", "salud": "💊",
    "entretenimiento": "🎬", "hogar": "🏠", "ropa": "👕",
    "tecnología": "💻", "educación": "📚", "suscripciones": "📱", "otro": "📦",
}


def fmt(monto: int) -> str:
    return f"${monto:,}".replace(",", ".")


def cat_emoji(cat: str) -> str:
    return CAT_EMOJI.get(cat.lower(), "📦")


def resumen_mes(user_id: int, anio: int, mes: int) -> str:
    rows = obtener_gastos_mes(user_id, anio, mes)
    if not rows:
        return f"📭 No hay gastos en {MESES[mes]}."

    personales = [r for r in rows if r["tipo"] == "personal"]
    splits = [r for r in rows if r["tipo"] == "split"]
    adelantos = [r for r in rows if r["tipo"] == "adelanto"]

    # Para splits, el gasto "tuyo" es monto_total menos lo que deben otros
    # Simplificamos: mostramos el total pagado y separamos adelantos
    total_pagado = sum(r["monto_total"] for r in rows)
    total_adelantos = sum(r["monto_total"] for r in adelantos)
    total_propio = total_pagado - total_adelantos

    # Categorías (solo gastos propios + splits, no adelantos)
    por_cat = defaultdict(int)
    for r in personales + splits:
        por_cat[r["categoria"]] += r["monto_total"]

    lineas = [f"📊 *Resumen de {MESES[mes]}*\n"]
    lineas.append("*Tus gastos:*")
    for cat, subtotal in sorted(por_cat.items(), key=lambda x: -x[1]):
        emoji = cat_emoji(cat)
        lineas.append(f"  {emoji} {cat}: {fmt(subtotal)}")

    lineas.append(f"\n💰 *Total propio: {fmt(total_propio)}*")

    if adelantos:
        lineas.append(f"\n↗️ *Adelantos por otros: {fmt(total_adelantos)}*")
        for r in adelantos:
            lineas.append(f"  • {r['descripcion'].capitalize()}: {fmt(r['monto_total'])}")

    lineas.append(f"\n🧾 *Total pagado con tarjeta: {fmt(total_pagado)}*")
    return "\n".join(lineas)


def resumen_categoria(user_id: int, categoria: str, anio: int, mes: int) -> str:
    rows = obtener_gastos_categoria(user_id, categoria, anio, mes)
    emoji = cat_emoji(categoria)
    if not rows:
        return f"{emoji} No hay gastos en *{categoria}* este mes."

    total = sum(r["monto_total"] for r in rows)
    lineas = [f"{emoji} *{categoria} — {MESES[mes]}*\n"]
    for r in rows:
        dia = r["fecha"][:10]
        lineas.append(f"• {r['descripcion'].capitalize()} — {fmt(r['monto_total'])} ({dia})")
    lineas.append(f"\n💰 *Total: {fmt(total)}*")
    return "\n".join(lineas)


def ultimos_gastos(user_id: int) -> str:
    rows = obtener_ultimos_gastos(user_id, 10)
    if not rows:
        return "📭 Aún no hay gastos registrados."

    lineas = [f"🧾 *Últimos {len(rows)} gastos*\n"]
    for r in rows:
        emoji = cat_emoji(r["categoria"])
        dia = r["fecha"][:10]
        tipo_tag = ""
        if r["tipo"] == "split":
            tipo_tag = " 👥"
        elif r["tipo"] == "adelanto":
            tipo_tag = " ↗️"
        lineas.append(f"{emoji} {r['descripcion'].capitalize()} — {fmt(r['monto_total'])}{tipo_tag} · {dia}")
    return "\n".join(lineas)


def deudas_todas(user_id: int) -> str:
    rows = obtener_deudas_por_persona(user_id)
    if not rows:
        return "✅ Nadie te debe nada."

    total = sum(r["total"] for r in rows)
    lineas = ["👥 *Te deben*\n"]
    for r in rows:
        lineas.append(f"• {r['persona'].capitalize()}: {fmt(r['total'])}")
    lineas.append(f"\n💰 *Total: {fmt(total)}*")
    return "\n".join(lineas)


def deuda_persona(user_id: int, persona: str) -> str:
    rows = obtener_deuda_persona(user_id, persona)
    if not rows:
        return f"✅ {persona.capitalize()} no te debe nada."

    total = sum(r["monto"] for r in rows)
    lineas = [f"👤 *{persona.capitalize()} te debe {fmt(total)}*\n"]
    for r in rows:
        dia = r["fecha"][:10]
        lineas.append(f"• {r['descripcion'].capitalize()} — {fmt(r['monto'])} ({dia})")
    return "\n".join(lineas)


def comparar_meses(user_id: int) -> str:
    now = datetime.now()
    mes_actual = now.month
    anio_actual = now.year
    mes_ant = mes_actual - 1 if mes_actual > 1 else 12
    anio_ant = anio_actual if mes_actual > 1 else anio_actual - 1

    datos = obtener_gastos_multiples_meses(user_id, [(anio_ant, mes_ant), (anio_actual, mes_actual)])

    def procesar(rows):
        total = sum(r["monto_total"] for r in rows if r["tipo"] != "adelanto")
        por_cat = defaultdict(int)
        for r in rows:
            if r["tipo"] != "adelanto":
                por_cat[r["categoria"]] += r["monto_total"]
        return total, por_cat

    total_ant, cat_ant = procesar(datos[(anio_ant, mes_ant)])
    total_act, cat_act = procesar(datos[(anio_actual, mes_actual)])

    if not total_ant and not total_act:
        return "📭 No hay datos suficientes para comparar."

    diff = total_act - total_ant
    signo = "+" if diff > 0 else ""
    emoji_diff = "📈" if diff > 0 else "📉"

    lineas = [f"📊 *{MESES[mes_ant].capitalize()} vs {MESES[mes_actual].capitalize()}*\n"]
    lineas.append(f"  {MESES[mes_ant].capitalize()}: {fmt(total_ant)}")
    lineas.append(f"  {MESES[mes_actual].capitalize()}: {fmt(total_act)}")
    lineas.append(f"  {emoji_diff} Diferencia: {signo}{fmt(abs(diff))}\n")

    # Categorías que aparecen en alguno de los dos
    todas_cats = set(cat_ant.keys()) | set(cat_act.keys())
    lineas.append("*Por categoría:*")
    for cat in sorted(todas_cats):
        v_ant = cat_ant.get(cat, 0)
        v_act = cat_act.get(cat, 0)
        d = v_act - v_ant
        signo_c = "+" if d > 0 else ""
        emoji = cat_emoji(cat)
        lineas.append(f"  {emoji} {cat}: {fmt(v_ant)} → {fmt(v_act)} ({signo_c}{fmt(abs(d))})")

    return "\n".join(lineas)


def metricas(user_id: int) -> str:
    now = datetime.now()
    mes = now.month
    anio = now.year

    rows = obtener_gastos_mes(user_id, anio, mes)
    if not rows:
        return "📭 No hay datos este mes para analizar."

    propios = [r for r in rows if r["tipo"] != "adelanto"]
    total = sum(r["monto_total"] for r in propios)
    if total == 0:
        return "📭 No hay gastos propios este mes."

    por_cat = defaultdict(int)
    for r in propios:
        por_cat[r["categoria"]] += r["monto_total"]

    lineas = [f"📈 *Métricas de {MESES[mes]}*\n"]
    lineas.append("*Porcentaje por categoría:*")
    for cat, monto in sorted(por_cat.items(), key=lambda x: -x[1]):
        pct = round(monto / total * 100)
        bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
        emoji = cat_emoji(cat)
        lineas.append(f"  {emoji} {cat}\n    {bar} {pct}% — {fmt(monto)}")

    # Gasto promedio diario
    dia_actual = now.day
    promedio_diario = total // dia_actual
    lineas.append(f"\n📅 Promedio diario: {fmt(promedio_diario)}")

    # Proyección fin de mes
    dias_mes = 30
    proyeccion = promedio_diario * dias_mes
    lineas.append(f"🔮 Proyección fin de mes: {fmt(proyeccion)}")

    return "\n".join(lineas)
