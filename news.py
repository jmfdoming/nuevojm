import streamlit as st
import yfinance as yf
from transformers import pipeline
import plotly.express as px
import pandas as pd
import requests
from datetime import datetime, timedelta

# Configuración de la página
st.set_page_config(page_title="Análisis Avanzado de Sentimiento de Noticias", layout="wide")
st.title("📈 Análisis Avanzado de Sentimiento de Noticias de Compañías")
st.sidebar.header("🔎 Parámetros de Entrada")

# Entrada del ticker de la compañía
ticker = st.sidebar.text_input("Ingrese el ticker de la compañía", value='AAPL')

# Selección de la ventana temporal
st.sidebar.subheader("🗓️ Seleccione el rango de fechas")
start_date = st.sidebar.date_input("Fecha de inicio", datetime.today() - timedelta(days=7))
end_date = st.sidebar.date_input("Fecha de fin", datetime.today())

# Filtros adicionales para las noticias
st.sidebar.subheader("📰 Filtros de Noticias")
news_limit = st.sidebar.slider("Número máximo de noticias", min_value=10, max_value=100, value=50, step=10)
keywords = st.sidebar.text_input("Palabras clave (separadas por comas)", value='')

# Selección del modelo de análisis de sentimiento
st.sidebar.subheader("🧠 Seleccione el modelo de análisis")
model_options = {
    "Modelo General (Multilingüe)": "nlptown/bert-base-multilingual-uncased-sentiment",
    "Modelo Financiero (FinBERT)": "ProsusAI/finbert",
    "Detección de Emociones": "j-hartmann/emotion-english-distilroberta-base"
}
model_choice = st.sidebar.selectbox("Modelo de Sentimiento", list(model_options.keys()))

if ticker:
    # Obtener información de la compañía usando yfinance
    try:
        stock = yf.Ticker(ticker)
        stock_info = stock.info

        if not stock_info:
            st.error("Ticker no válido o no se pudo obtener información. Por favor, ingrese un ticker válido.")
            st.stop()

        company_name = stock_info.get('longName') or stock_info.get('shortName') or ticker

    except Exception as e:
        st.error("Error al obtener información del ticker. Por favor, ingrese un ticker válido.")
        st.stop()

    # Configuración de EODHD
    api_token = '61f1787073aff1.66026778'  # Reemplaza con tu clave de API de EODHD
    base_url = 'https://eodhistoricaldata.com/api/news'

    # Convertir fechas a formato requerido
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    # Obtener noticias relacionadas con la compañía
    params = {
        'api_token': api_token,
        's': ticker,
        'from': start_date_str,
        'to': end_date_str,
        'limit': news_limit
    }

    if keywords:
        params['q'] = keywords

    try:
        response = requests.get(base_url, params=params)
        articles = response.json()
    except Exception as e:
        st.error("Error al obtener noticias de EODHD. Por favor, verifica tu clave de API y la conexión a internet.")
        st.stop()

    if articles and isinstance(articles, list):
        st.header(f"📰 Noticias de {company_name} desde {start_date_str} hasta {end_date_str}")

        # Configuración del análisis de sentimiento
        selected_model = model_options[model_choice]
        if selected_model == "ProsusAI/finbert":
            sentiment_pipeline = pipeline('sentiment-analysis', model='ProsusAI/finbert')
            sentiment_labels = {'positive': 1, 'negative': -1, 'neutral': 0}
        elif selected_model == "j-hartmann/emotion-english-distilroberta-base":
            sentiment_pipeline = pipeline('text-classification', model='j-hartmann/emotion-english-distilroberta-base', return_all_scores=False)
            # Emociones específicas
        else:
            sentiment_pipeline = pipeline('sentiment-analysis', model='nlptown/bert-base-multilingual-uncased-sentiment')
            sentiment_labels = {
                '1 star': 1,
                '2 stars': 2,
                '3 stars': 3,
                '4 stars': 4,
                '5 stars': 5
            }

        sentiments = []

        for article in articles:
            title = article.get('title', 'Sin título')
            content = article.get('content', '')
            link = article.get('link', '#')
            date_published = article.get('date', '')

            # Realizar análisis de sentimiento en el contenido
            if content:
                try:
                    if selected_model == "j-hartmann/emotion-english-distilroberta-base":
                        sentiment = sentiment_pipeline(content[:512])[0]
                        label = sentiment['label']
                        score = sentiment['score']
                    else:
                        sentiment = sentiment_pipeline(content[:512])[0]
                        label = sentiment['label']
                        score = sentiment['score']
                except:
                    label = 'Neutral'
                    score = 0.0
            else:
                label = 'Neutral'
                score = 0.0

            # Almacenar resultados
            sentiments.append({
                'Fecha': date_published,
                'Título': title,
                'Sentimiento': label,
                'Score': score,
                'Link': link
            })

        # Convertir a DataFrame
        df = pd.DataFrame(sentiments)

        # Mostrar noticias y sus sentimientos
        for index, row in df.iterrows():
            st.subheader(f"{row['Título']} ({row['Fecha']})")
            st.write(f"**Sentimiento:** {row['Sentimiento']} (Score: {row['Score']:.2f})")
            st.markdown(f"[Leer más]({row['Link']})")
            st.markdown("---")

        # Mejorar el gráfico de resumen del sentimiento
        st.subheader("📊 Visualizaciones de Sentimiento")

        # Gráfico de barras de sentimiento
        sentiment_counts = df['Sentimiento'].value_counts().reset_index()
        sentiment_counts.columns = ['Sentimiento', 'Cantidad']

        fig_bar = px.bar(sentiment_counts, x='Sentimiento', y='Cantidad',
                         color='Sentimiento', title='Distribución del Sentimiento',
                         color_discrete_sequence=px.colors.qualitative.Set2)
        st.plotly_chart(fig_bar, use_container_width=True)

        # Gráfico de tarta en la barra lateral
        with st.sidebar:
            st.markdown("---")
            st.subheader("📊 Distribución del Sentimiento")
            fig_pie = px.pie(sentiment_counts, values='Cantidad', names='Sentimiento',
                             color_discrete_sequence=px.colors.qualitative.Set3)
            st.plotly_chart(fig_pie, use_container_width=True)

        # Gráfico de tendencia del sentimiento a lo largo del tiempo
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        df = df.sort_values('Fecha')

        if selected_model != "j-hartmann/emotion-english-distilroberta-base":
            # Asignar valores numéricos al sentimiento
            df['Sentimiento_Num'] = df['Sentimiento'].map(sentiment_labels)
            fig_line = px.line(df, x='Fecha', y='Sentimiento_Num', markers=True,
                               title='Tendencia del Sentimiento en el Tiempo')
            fig_line.update_yaxes(title_text='Sentimiento (Numérico)')
            st.plotly_chart(fig_line, use_container_width=True)

            # Sentimiento promedio
            average_sentiment = df['Sentimiento_Num'].mean()
            st.sidebar.markdown(f"## Sentimiento promedio: {average_sentiment:.2f}")
        else:
            # Mostrar emociones a lo largo del tiempo
            fig_line = px.scatter(df, x='Fecha', y='Sentimiento', size='Score',
                                  color='Sentimiento', title='Emociones en el Tiempo')
            st.plotly_chart(fig_line, use_container_width=True)

    else:
        st.warning("No se encontraron noticias para esta compañía en el rango de fechas seleccionado.")
