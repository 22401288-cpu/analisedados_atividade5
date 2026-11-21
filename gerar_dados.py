import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

FUSO = 'America/Sao_Paulo'
NIVEIS_RISCO = {
    'C100': 'Baixo',
    'C101': 'Alto',
    'C102': 'Médio',
    'C103': 'Baixo',
    'C104': 'Alto',
}


def carregar_transacoes(caminho):
    dados = pd.read_csv(caminho, encoding='latin1')
    mediana_estado = dados.groupby('estado_cliente')['valor'].transform('median')
    dados['valor'] = dados['valor'].fillna(mediana_estado)
    dados['plataforma'] = 'Mobile'
    return dados


def carregar_cotacoes(caminho):
    cotacoes = pd.read_csv(caminho, encoding='utf-8')
    cotacoes['cotacao_usd'] = cotacoes['cotacao_usd'].interpolate(method='linear')
    cotacoes['data'] = pd.to_datetime(cotacoes['data'])
    return cotacoes


def preparar_datas(dados):
    datas = pd.to_datetime(dados['data_transacao']).dt.tz_localize(FUSO)
    dados = dados.assign(data_transacao=datas)
    dados['dia_semana'] = dados['data_transacao'].dt.day_name()
    dados['mes'] = dados['data_transacao'].dt.month
    return dados.drop_duplicates(keep='first').reset_index(drop=True)


def filtrar_setembro_alto_valor(dados):
    em_setembro = dados['mes'].eq(9)
    estados_alvo = dados['estado_cliente'].isin(['SP', 'RJ'])
    valor_alto = dados['valor'].gt(5000.0)
    return dados.loc[em_setembro & estados_alvo & valor_alto].copy()


def integrar_cotacoes(dados, cotacoes):
    dados = dados.copy()
    dados['nivel_risco'] = dados['id_cliente'].map(NIVEIS_RISCO)
    dados['data_apenas'] = pd.to_datetime(dados['data_transacao'].dt.date)
    unido = dados.merge(
        cotacoes[['data', 'cotacao_usd']],
        how='left',
        left_on='data_apenas',
        right_on='data',
    )
    unido['valor_usd'] = (unido['valor'] / unido['cotacao_usd']).round(2)
    return unido


def montar_pivot(unido):
    return pd.pivot_table(
        unido,
        values='valor',
        index='mes',
        columns='nivel_risco',
        aggfunc='sum',
        margins=True,
        margins_name='Total',
    )


def detectar_anomalias(unido, limite=2.5):
    grupo = unido.groupby('estado_cliente')['valor']
    z = (unido['valor'] - grupo.transform('mean')) / grupo.transform('std')
    unido = unido.assign(z_score=z)
    return unido, unido.loc[unido['z_score'] > limite].copy()


def serie_diaria(unido):
    diario = (
        unido.assign(dia=unido['data_transacao'].dt.date)
        .groupby('dia', as_index=False)['valor']
        .sum()
    )
    diario['dia'] = pd.to_datetime(diario['dia'])
    diario = diario.sort_values('dia').reset_index(drop=True)
    diario['media_movel_7d'] = diario['valor'].rolling(7, min_periods=1).mean()
    return diario


def desenhar_grafico(diario, destino='relatorio_transacoes.png'):
    fig, ax = plt.subplots(figsize=(12, 5.5))

    ax.plot(
        diario['dia'],
        diario['valor'],
        color='#0055d4',
        linewidth=1.8,
        marker='o',
        markersize=3.5,
        label='Valor Total Diário (R$)',
    )
    ax.plot(
        diario['dia'],
        diario['media_movel_7d'],
        color='#ff7f0e',
        linewidth=2.5,
        linestyle='--',
        label='Média Móvel (7 Dias)',
    )

    ax.set_ylim(bottom=0)
    ax.set_title(
        'Evolução Diária do Volume Transacionado e Média Móvel (7d)',
        fontsize=13,
        fontweight='bold',
        pad=15,
    )
    ax.set_xlabel('Data', fontsize=10)
    ax.set_ylabel('Valor Total (R$)', fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='upper right', frameon=True)
    ax.tick_params(axis='x', rotation=35)

    fig.tight_layout()
    fig.savefig(destino, dpi=300)
    plt.show()


def executar_pipeline():
    transacoes = carregar_transacoes('transacoes.csv')
    cotacoes = carregar_cotacoes('cotacoes.csv')

    transacoes = preparar_datas(transacoes)
    setembro_alto = filtrar_setembro_alto_valor(transacoes)

    unido = integrar_cotacoes(transacoes, cotacoes)
    pivot = montar_pivot(unido)
    unido, anomalias = detectar_anomalias(unido)

    desenhar_grafico(serie_diaria(unido))

    return pivot, anomalias, setembro_alto


if __name__ == '__main__':
    tabela_pivot, df_anomalias, df_setembro = executar_pipeline()