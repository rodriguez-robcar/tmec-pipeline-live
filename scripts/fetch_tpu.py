"""
Descarga el índice TPU (Trade Policy Uncertainty) más reciente y lo sube a Supabase.

Variables de entorno esperadas (se configuran como GitHub Secrets, ver README):
    DATABASE_URL -> connection string de Supabase
"""
import os
import io
import requests
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

TPU_URL = "https://www.matteoiacoviello.com/tpu_files/tpu_web_latest.xlsx"


def construir_engine():
    """
    Arma la URL de conexión por partes con sqlalchemy.engine.URL.create,
    que codifica automáticamente cualquier caracter especial en la contraseña
    (@, #, %, /, etc.).

    Espera estas variables de entorno (GitHub Secrets o export local):
        DB_USER, DB_PASSWORD, DB_HOST, DB_PORT (opcional, default 5432), DB_NAME (opcional, default postgres)
    """
    url = URL.create(
        drivername="postgresql+psycopg2",
        username=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        host=os.environ["DB_HOST"],
        port=int(os.environ.get("DB_PORT", 5432)),
        database=os.environ.get("DB_NAME", "postgres"),
    )
    return create_engine(url)


def descargar_tpu() -> pd.DataFrame:
    headers = {"User-Agent": "Mozilla/5.0 (compatible; RobertoDataPipeline/1.0)"}
    resp = requests.get(TPU_URL, headers=headers, timeout=30)
    resp.raise_for_status()

    df = pd.read_excel(io.BytesIO(resp.content), sheet_name="TPU_MONTHLY")
    df["fecha"] = pd.to_datetime(df["DATE"]).dt.to_period("M").dt.to_timestamp()
    df = df[["fecha", "TPU"]].rename(columns={"TPU": "tpu_valor"})
    df = df.dropna(subset=["tpu_valor"])
    return df


def subir_a_supabase(df: pd.DataFrame, filas_recientes: int = 6):
    """Sube solo los últimos N meses (evita reescribir 60+ años cada corrida)."""
    df_reciente = df.sort_values("fecha").tail(filas_recientes)

    engine = construir_engine()
    with engine.begin() as conn:
        for _, row in df_reciente.iterrows():
            conn.execute(text("""
                INSERT INTO tpu_mensual (fecha, tpu_valor, fecha_actualizacion)
                VALUES (:fecha, :tpu_valor, now())
                ON CONFLICT (fecha)
                DO UPDATE SET tpu_valor = EXCLUDED.tpu_valor,
                              fecha_actualizacion = now()
            """), {"fecha": row["fecha"].date(), "tpu_valor": float(row["tpu_valor"])})

    print(f"TPU: {len(df_reciente)} filas insertadas/actualizadas "
          f"({df_reciente['fecha'].min().date()} a {df_reciente['fecha'].max().date()})")


if __name__ == "__main__":
    df = descargar_tpu()
    print(f"Descargados {len(df)} meses de TPU. Último dato: {df.iloc[-1].to_dict()}")
    subir_a_supabase(df)
