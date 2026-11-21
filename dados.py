import numpy as np
import pandas as pd

SEMENTE = 42
TOTAL_LINHAS = 1000
DUPLICADAS = 15

np.random.seed(SEMENTE)


def gerar_transacoes(caminho):
    horarios = pd.date_range('2026-09-01', periods=TOTAL_LINHAS, freq='h')

    tabela = pd.DataFrame({
        'id_cliente': np.random.choice(
            ['C100', 'C101', 'C102', 'C103', 'C104'], size=TOTAL_LINHAS
        ),
        'data_transacao': horarios,
        'valor': np.random.choice(
            [np.nan, 150.0, 3000.0, 7500.0, 12000.0, 50.0],
            size=TOTAL_LINHAS,
            p=[0.05, 0.40, 0.30, 0.15, 0.05, 0.05],
        ),
        'estado_cliente': np.random.choice(
            ['SP', 'RJ', 'MG', 'RS'], size=TOTAL_LINHAS
        ),
        'origem': np.random.choice(
            ['web', 'mobile_app', 'atm'], size=TOTAL_LINHAS
        ),
    })

    tabela = pd.concat([tabela, tabela.head(DUPLICADAS)], ignore_index=True)
    tabela.to_csv(caminho, index=False, encoding='latin1')


def gerar_cotacoes(caminho):
    dias = pd.date_range('2026-09-01', '2026-10-01', freq='D')

    retornos = np.random.normal(0.001, 0.015, len(dias))
    serie = 5.20 * np.exp(retornos.cumsum())

    tabela = pd.DataFrame({
        'data': dias,
        'cotacao_usd': serie.round(4),
        'volume_negociado': np.random.randint(10000, 500000, len(dias)),
    })

    tabela.loc[[5, 18], 'cotacao_usd'] = np.nan
    tabela.to_csv(caminho, index=False, encoding='utf-8')


if __name__ == '__main__':
    gerar_transacoes('transacoes.csv')
    gerar_cotacoes('cotacoes.csv')
    print("Arquivos 'transacoes.csv' e 'cotacoes.csv' gerados com sucesso!")