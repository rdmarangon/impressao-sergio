import os
import pandas as pd
import sqlite3
from pathlib import Path

# =====================================================

# CONFIGURAÇÕES

# =====================================================

PASTA_DADOS = Path(".")

BANCO_SQLITE = os.environ.get("DB_PATH", "impressoras.db")

ARQUIVOS = [
    ("impressos_2024.xlsx", 2024),
    ("Impressos_2025.xlsx", 2025),
    ("Impressos_2026.xlsx", 2026),
]

MESES = {
    "Jan": 1,
    "Fev": 2,
    "Mar": 3,
    "Abr": 4,
    "Mai": 5,
    "Jun": 6,
    "Jul": 7,
    "Ago": 8,
    "Set": 9,
    "Out": 10,
    "Nov": 11,
    "Dez": 12,
}

# =====================================================

# CONEXÃO SQLITE

# =====================================================

conn = sqlite3.connect(BANCO_SQLITE)
cursor = conn.cursor()

# Apaga tabela antiga (se existir)

cursor.execute("""
DROP TABLE IF EXISTS consumo_impressoras
""")

# Cria tabela

cursor.execute("""
CREATE TABLE consumo_impressoras (
id INTEGER PRIMARY KEY AUTOINCREMENT,
ano INTEGER,
mes INTEGER,
serial TEXT,
controle TEXT,
local TEXT,
tipo TEXT,
paginas INTEGER
)
""")

# =====================================================

# IMPORTAÇÃO

# =====================================================

total_registros = 0

for arquivo, ano in ARQUIVOS:

    caminho = PASTA_DADOS / arquivo

    print(f"\nProcessando: {arquivo}")

    df = pd.read_excel(caminho)

    # Padroniza nomes das colunas
    df.columns = [str(col).strip() for col in df.columns]

    # Corrige diferenças de nomenclatura
    df.rename(columns={"Maio": "Mai"}, inplace=True)

    # Remove linhas totalmente vazias
    df = df.dropna(how="all")

    # Reinicia índices
    df = df.reset_index(drop=True)

    registros = []

    for idx, row in df.iterrows():

        # Primeiras 6 linhas = Tipo III
        tipo = "III" if idx < 6 else "I"

        serial = str(row["SERIAL"]).strip()
        controle = str(row["Controle"]).strip()
        local = str(row["LOCAL"]).strip()

        for mes_nome, mes_numero in MESES.items():

            # Ignora mês inexistente
            if mes_nome not in df.columns:
                continue

            valor = row[mes_nome]

            # Ignora células vazias
            if pd.isna(valor):
                continue

            try:
                paginas = int(valor)
            except:
                continue

            registros.append((ano, mes_numero, serial, controle, local, tipo, paginas))

    cursor.executemany(
        """
        INSERT INTO consumo_impressoras (
            ano,
            mes,
            serial,
            controle,
            local,
            tipo,
            paginas
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        registros,
    )

    total_registros += len(registros)

    print(f"  {len(registros)} registros importados")

# =====================================================

# ÍNDICES

# =====================================================

cursor.execute("""
CREATE INDEX IF NOT EXISTS idx_serial
ON consumo_impressoras(serial)
""")

cursor.execute("""
CREATE INDEX IF NOT EXISTS idx_local
ON consumo_impressoras(local)
""")

cursor.execute("""
CREATE INDEX IF NOT EXISTS idx_tipo
ON consumo_impressoras(tipo)
""")

cursor.execute("""
CREATE INDEX IF NOT EXISTS idx_ano
ON consumo_impressoras(ano)
""")

# =====================================================

# FINALIZA

# =====================================================

conn.commit()
conn.execute("VACUUM")

print("\n" + "=" * 50)
print("IMPORTAÇÃO CONCLUÍDA")
print(f"TOTAL DE REGISTROS: {total_registros}")
print("=" * 50)

conn.close()
