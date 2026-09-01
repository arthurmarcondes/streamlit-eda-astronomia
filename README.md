# Análise de Estrelas — App Streamlit

## Como rodar

1. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```
2. Coloque o arquivo `cleaned_star_data.csv` na mesma pasta que `app.py`.
3. Execute:
   ```
   streamlit run app.py
   ```

## O que o app faz

Reproduz e expande a análise exploratória do notebook original:

- **Estrutura do dataset**: dimensões, tipos de coluna, amostra dos dados.
- **Estatísticas descritivas**: `describe()` interativo.
- **Filtros na barra lateral**: por tipo de estrela, cor e faixa de temperatura.
- **Distribuição dos tipos e cores**: gráfico de barras e pizza.
- **Distribuição da temperatura**: boxplot e histograma.
- **Diagrama H-R**: temperatura x luminosidade (escala log, eixo invertido como
  na convenção astronômica), com tamanho dos pontos proporcional ao raio.
- **Matriz de correlação**: entre temperatura, luminosidade, raio e magnitude
  absoluta.

Todos os gráficos são interativos (Plotly) e respondem aos filtros escolhidos.
