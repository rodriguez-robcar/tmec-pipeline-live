
Pipeline de datos automatizado que mantiene actualizados, cada semana y sin intervención
manual, dos indicadores clave para el análisis de sensibilidad del nearshoring en Querétaro
al T-MEC: el índice de incertidumbre comercial (TPU) y el tipo de cambio MXN/USD.

Es parte del proyecto exploratorio
[queretaro-tmec-sensitivity](https://github.com/rodriguez-robcar/queretaro-tmec-sensitivity) — mismo tema, ahora con un
pipeline que corre solo.

## Arquitectura

```
GitHub Actions (cron semanal, lunes 09:00 UTC)
        │
        ├── scripts/fetch_tpu.py  ──> Fed / Caldara-Iacoviello (archivo .xlsx)
        └── scripts/fetch_fx.py   ──> Banxico SIE API (serie SF43718)
                        │
                        ▼
              PostgreSQL en Supabase
                        │
                        ▼
                   Power BI (DirectQuery)

```

## Setup desde cero

1. Base de datos (Supabase)

    1. Crea proyecto gratis en supabase.com.
    2. En SQL Editor, corre sql/schema.sql una sola vez.
    3. En Connect → Connection string → Transaction pooler, copia el string. De ahí sacas:

        - DB_USER: postgres.<project-ref>
        - DB_HOST: aws-0-<región>.pooler.supabase.com
        - DB_PORT: 6543
        - DB_PASSWORD: password del proyecto en Supabase

2. Token de Banxico

    Se puede sacar en [banxico.org.mx/SieAPIRest/service/v1/token](https://www.banxico.org.mx/SieAPIRest/service/v1/token).

3. GitHub Secrets

    En el repo → Settings → Secrets and variables → Actions, crea:
DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, BANXICO_TOKEN.

4. Probar localmente

```
pip install -r requirements.txt
export DB_USER="postgres.xxxxx"
export DB_PASSWORD="tu_password"
export DB_HOST="aws-0-us-east-1.pooler.supabase.com"
export DB_PORT="6543"
export BANXICO_TOKEN="tu_token"

python scripts/fetch_tpu.py
python scripts/fetch_fx.py
```
   
5. Power BI

    Obtener datos → PostgreSQL database → servidor <DB_HOST>:<DB_PORT> → base postgres →
modo DirectQuery → usuario/contraseña → seleccionar tablas o la vista
vista_mensual_combinada.

## Troubleshooting

**Error**: could not translate host name "password@db...supabase.co"</br>
La contraseña tenía caracteres especiales que rompían el parseo de una URL de conexión
armada como string único. Solución: los scripts arman la conexión por partes con
sqlalchemy.engine.URL.create(), que codifica automáticamente cualquier caracter especial
— por eso las variables de entorno están separadas (DB_USER, DB_PASSWORD, etc.) en vez
de un solo DATABASE_URL.

**Error**: could not translate host name "db.<ref>.supabase.co"</br>
La conexión "Direct connection" de Supabase requiere soporte de IPv6, que muchas redes
domésticas no tienen habilitado. Solución: usar el Transaction pooler
(aws-0-<región>.pooler.supabase.com:6543) en vez de la conexión directa — funciona sobre
IPv4 normal. Nota: con el pooler, el usuario cambia de postgres a
postgres.<project-ref>.

## Estructura
```
├── scripts/
│   ├── fetch_tpu.py       # Descarga TPU mensual y hace upsert en Supabase
│   └── fetch_fx.py        # Descarga tipo de cambio diario (Banxico) y hace upsert
├── sql/
│   └── schema.sql         # Tablas + vista combinada (correr una sola vez)
├── .github/workflows/
│   └── update_data.yml    # Cron semanal + trigger manual
└── requirements.txt
```
## Autor
Roberto Rodríguez - extensión productiva del proyecto de portafolio [queretaro-tmec-sensitivity](https://github.com/rodriguez-robcar/queretaro-tmec-sensitivity)
