"""
Descarga el tipo de cambio MXN/USD (serie FIX, SF43718) de Banxico y lo sube a Supabase.

Requiere un token gratuito de Banxico en https://www.banxico.org.mx/SieAPIRest/service/v1/token

Variables de entorno esperadas (GitHub Secrets):
    BANXICO_TOKEN
    DATABASE_URL
"""
import os
import requests
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

SERIE_FIX = "SF43718"  # Tipo de cambio pesos por dólar, serie FIX
BANXICO_TOKEN = os.environ["BANXICO_TOKEN"]

def construir_engine():
    """Ver docstring equivalente en fetch_tpu.py."""
    url = URL.create(
        drivername="postgresql+psycopg2",
        username=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        host=os.environ["DB_HOST"],
        port=int(os.environ.get("DB_PORT", 5432)),
        database=os.environ.get("DB_NAME", "postgres"),
    )
    return create_engine(url)


def descargar_tipo_cambio(dias_atras: int = 10) -> pd.DataFrame:
    """Trae los datos más recientes (últimos N días hábiles disponibles)."""
    url = (
        f"https://www.banxico.org.mx/SieAPIRest/service/v1/series/{SERIE_FIX}"
        f"/datos/oportuno"
    )
    headers = {"Bmx-Token": BANXICO_TOKEN}
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()

    datos = resp.json()["bmx"]["series"][0]["datos"]
    df = pd.DataFrame(datos)
    df["fecha"] = pd.to_datetime(df["fecha"], format="%d/%m/%Y")
    df["mxn_por_usd"] = pd.to_numeric(df["dato"], errors="coerce")
    df = df.dropna(subset=["mxn_por_usd"])
    return df[["fecha", "mxn_por_usd"]]


def subir_a_supabase(df: pd.DataFrame):
    engine = create_engine(DATABASE_URL)
    with engine.begin() as conn:
        for _, row in df.iterrows():
            conn.execute(text("""
                INSERT INTO tipo_cambio_diario (fecha, mxn_por_usd, fecha_actualizacion)
                VALUES (:fecha, :valor, now())
                ON CONFLICT (fecha)
                DO UPDATE SET mxn_por_usd = EXCLUDED.mxn_por_usd,
                              fecha_actualizacion = now()
            """), {"fecha": row["fecha"].date(), "valor": float(row["mxn_por_usd"])})

    print(f"Tipo de cambio: {len(df)} filas insertadas/actualizadas")


if __name__ == "__main__":
    df = descargar_tipo_cambio()
    print(f"Descargados {len(df)} días. Último dato: {df.iloc[-1].to_dict()}")
    subir_a_supabase(df)
