import os
import sqlite3
import pandas as pd

# --- CONFIGURAÇÕES DO PROJETO ---
ARQUIVO_EXCEL = "Impressos_2026.xlsx"
NOME_BANCO = os.environ.get("DB_PATH", "impressoras.db")  # default: pasta do script
NOME_TABELA = "consumo_impressoras"


def importar_dados_junho():
    # 1. Verifica se o arquivo de junho está na pasta
    if not os.path.exists(ARQUIVO_EXCEL):
        print(f"❌ Erro: O arquivo '{ARQUIVO_EXCEL}' não foi encontrado nesta pasta.")
        return

    print(f"📂 Carregando os dados de {ARQUIVO_EXCEL}...")
    df_excel = pd.read_excel(ARQUIVO_EXCEL)

    print(
        "🔄 Processando e transformando a estrutura da planilha para o banco de dados..."
    )

    try:
        # 2. Criamos um novo DataFrame contendo apenas o que o banco precisa para o mês de Junho
        df_migracao = pd.DataFrame()

        # Mapeamento Direto de colunas existentes
        df_migracao["serial"] = df_excel["SERIAL"]
        df_migracao["controle"] = df_excel["Controle"]
        df_migracao["local"] = df_excel["LOCAL"]

        # Direciona os dados da coluna 'Jun' para a coluna 'paginas' do banco
        df_migracao["paginas"] = df_excel["Jun"].fillna(0).astype(int)

        # Injeção de Valores Fixos estipulados por você
        df_migracao["ano"] = 2026
        df_migracao["mes"] = 6

        # ====================================================================
        # NOVA REGRA DO TIPO:
        # 'III' para as 6 primeiras linhas (índices < 6), 'I' para o restante
        # ====================================================================
        df_migracao["tipo"] = ["III" if i < 6 else "I" for i in range(len(df_migracao))]

        # Reorganiza as colunas exatamente na ordem que o banco espera
        df_migracao = df_migracao[
            ["ano", "mes", "serial", "controle", "local", "tipo", "paginas"]
        ]

        # Alterei para mostrar as 8 primeiras linhas para você ver a transição do III para o I na prévia
        print(f"📊 Prévia dos dados prontos para o banco:\n{df_migracao.head(8)}")

        # 3. Conexão e Inserção no Banco de Dados
        print(f"🔗 Conectando ao banco de dados {NOME_BANCO}...")
        conn = sqlite3.connect(NOME_BANCO)

        print("🚀 Inserindo os dados transformados no banco...")
        # Inserindo dados convertidos
        df_migracao.to_sql(NOME_TABELA, conn, if_exists="append", index=False)

        print(
            f"✅ Sucesso! Os dados da coluna 'Jun' da planilha foram migrados com sucesso para a tabela do banco."
        )

        conn.commit()
        conn.execute("VACUUM")

    except KeyError as e:
        print(
            f"\n❌ Erro de Mapeamento: Não foi possível encontrar a coluna {e} na sua planilha."
        )
        print(f"Colunas reais encontradas na planilha: {list(df_excel.columns)}")
    except Exception as e:
        print(f"\n❌ Erro crítico na migração: {e}")
    finally:
        if "conn" in locals():
            conn.close()
            print("🔌 Conexão com o banco de dados fechada.")


if __name__ == "__main__":
    importar_dados_junho()
