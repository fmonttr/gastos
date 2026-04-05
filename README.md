# 💸 Bot de Gastos — Telegram

Bot personal para registrar gastos de tarjeta de crédito (CMR Falabella) y débito (Itaú), con split de gastos, adelantos, y métricas mensuales.

---

## Qué puede hacer

### Registrar gastos
| Lo que escribís | Qué hace |
|---|---|
| `5000 oxxo` | Gasto personal, crédito por defecto |
| `10000 falabella débito` | Gasto personal con débito |
| `23000 mcdonalds, tomás y flo` | Split en partes iguales (3 personas) |
| `10000 flo, 13000 tomás mcdonalds` | Split con montos específicos |
| `15000 doctor, mamá` | Adelanto: lo pagaste vos, lo debe mamá |

### Consultas
| Lo que escribís | Qué hace |
|---|---|
| `¿cuánto gasté este mes?` | Resumen mensual (propios vs adelantos) |
| `¿cuánto gasté en comida?` | Gastos de una categoría |
| `¿cuánto me deben?` | Todas las deudas pendientes |
| `¿qué me debe tomás?` | Deuda de una persona específica |
| `tomás me pagó` | Marca toda la deuda de Tomás como pagada |
| `flo me pagó 5000` | Pago parcial |
| `últimos gastos` | Historial reciente |
| `métricas` | Porcentajes por categoría + proyección del mes |
| `compara meses` | Este mes vs el anterior |

---

## Setup

### 1. Crear el bot en Telegram
1. Abrí Telegram → buscá `@BotFather`
2. Escribí `/newbot` y seguí los pasos
3. Copiá el **token** que te da

### 2. Obtener Gemini API Key (gratis)
1. Entrá a [aistudio.google.com](https://aistudio.google.com)
2. Click en **Get API Key** → **Create API key**
3. Copiá la key

### 3. Deploy en Railway
1. Subí esta carpeta a un repositorio de GitHub
2. Entrá a [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo**
3. Conectá el repositorio
4. En **Variables**, agregá:
   - `TELEGRAM_TOKEN` = token del paso 1
   - `GEMINI_API_KEY` = key del paso 2
5. En **Settings** → **Start Command**: `python bot.py`
6. ¡Listo!

### Correr localmente (para probar)
```bash
pip install -r requirements.txt
export TELEGRAM_TOKEN="tu_token"
export GEMINI_API_KEY="tu_key"
python bot.py
```

---

## Estructura
```
gastos-bot/
├── bot.py          # Entry point de Telegram
├── handler.py      # Lógica principal, orquesta todo
├── ai.py           # Parser con Gemini
├── database.py     # SQLite: gastos y deudas
├── queries.py      # Formatea respuestas
└── requirements.txt
```

---

## Variables de entorno
| Variable | Descripción |
|---|---|
| `TELEGRAM_TOKEN` | Token del bot (BotFather) |
| `GEMINI_API_KEY` | API Key de Google Gemini |
| `DB_PATH` | Ruta de la base de datos (opcional, default: `gastos.db`) |
