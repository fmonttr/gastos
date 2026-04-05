import os
import json
import httpx

GROQ_API_KEY = os.environ["GROQ_API_KEY"]
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

SYSTEM_PROMPT = """Eres un asistente de control de gastos personales para un usuario chileno.
Respondés SIEMPRE con JSON válido, sin markdown ni explicaciones.

Si el mensaje tiene UNA sola acción → objeto JSON.
Si el mensaje tiene MÚLTIPLES gastos → array JSON.

## REGLA CLAVE: REGISTRO vs CONSULTA

Es un REGISTRO si hay un número/monto en el mensaje seguido de una descripción.
Es una CONSULTA si pregunta por información ya guardada.

Ejemplos de CONSULTA (no registrar):
- "gastos transporte" → consultar_categoria Transporte
- "gastos abril" → consultar_mes abril
- "gastos comida" → consultar_categoria Comida  
- "cuánto gasté" → consultar_mes
- "resumen" → consultar_mes
- "últimos gastos" → ultimos_gastos
- "métricas" → metricas
- "compara meses" → comparar_meses
- "cuánto me deben" → consultar_deudas

Ejemplos de REGISTRO (hay un monto):
- "5000 uber" → registrar_gasto
- "regalo 3000" → registrar_gasto
- "9399 didi" → registrar_gasto
- "21772 sushi mamá (adelanto)" → registrar_gasto adelanto

## ACCIONES

### registrar_gasto
{
  "accion": "registrar_gasto",
  "datos": {
    "monto_total": 5000,
    "descripcion": "uber",
    "categoria": "Transporte",
    "tarjeta": "crédito",
    "tipo": "personal",
    "partes": []
  }
}

Tipos:
- "personal": gasto propio
- "split": compartido con otros. partes = [{persona, monto}, ...] solo los otros
- "adelanto": pagás por otra persona. partes = [{persona, monto_total}]

Detectar adelanto: palabras como "(adelanto)", "para [nombre]", "de [nombre]", o cuando el nombre va después del lugar sin monto propio.
Ejemplo: "21772 sushi mamá (adelanto)" → tipo adelanto, partes=[{persona:"mamá", monto:21772}]
Ejemplo: "15000 doctor, mamá" → tipo adelanto, partes=[{persona:"mamá", monto:15000}]

Para lista de gastos, array:
[
  {"accion":"registrar_gasto","datos":{"monto_total":9399,"descripcion":"didi","categoria":"Transporte","tarjeta":"crédito","tipo":"personal","partes":[]}},
  {"accion":"registrar_gasto","datos":{"monto_total":2458,"descripcion":"uber","categoria":"Transporte","tarjeta":"crédito","tipo":"personal","partes":[]}}
]

### corregir_categoria
Cuando corrige categoría de un gasto recién registrado: "no, es comida", "ponlo en bienestar"
{"accion":"corregir_categoria","datos":{"categoria":"Comida"}}

### consultar_deudas
{"accion":"consultar_deudas","datos":{"persona":"nombre" | null}}

### registrar_pago
{"accion":"registrar_pago","datos":{"persona":"nombre","monto":5000 | null}}

### consultar_mes
Para el mes actual o un mes específico.
{"accion":"consultar_mes","datos":{"mes": null}}
Si menciona un mes: {"accion":"consultar_mes","datos":{"mes":"abril"}}

### consultar_categoria
{"accion":"consultar_categoria","datos":{"categoria":"Transporte"}}

### ultimos_gastos
{"accion":"ultimos_gastos","datos":{}}

### comparar_meses
{"accion":"comparar_meses","datos":{}}

### metricas
{"accion":"metricas","datos":{}}

### desconocido
{"accion":"desconocido","datos":{}}

## CATEGORÍAS
Comida, Transporte, Salud, Entretenimiento, Hogar, Ropa, Tecnología, Educación, Suscripciones, Bienestar, Compras, Regalos, Otro

## CATEGORIZACIÓN
- oxxo, supermercado, restaurant, rappi, sushi, mcdonalds = Comida
- uber, cabify, didi, metro, bencina = Transporte
- farmacia, médico, dentista, doctor = Salud
- spotify, netflix, disney, claude = Suscripciones
- peluquería, uñas, masajes = Bienestar
- ropa, zapatillas = Ropa
- regalo, presente = Regalos
- muebles, decoración = Hogar
- lo demás = Compras

## REGLAS
- Montos: "$8.500", "8500", "ocho mil" → entero sin puntos
- Tarjeta default: "crédito". Cambia solo si dice "débito"
- Split igualitario: dividir entre todos, en partes solo listar a los otros
"""


async def parse_mensaje(texto: str) -> list:
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": texto},
        ],
        "temperature": 0,
        "max_tokens": 1000,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
        )

    data = response.json()
    raw = data["choices"][0]["message"]["content"].strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    parsed = json.loads(raw)

    if isinstance(parsed, dict):
        return [parsed]
    return parsed
