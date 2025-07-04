import streamlit as st
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline

# Cache the model loading so it doesn't re-run on every interaction
@st.cache_resource
def load_sentiment_model():
    """Load and cache the FinBERT sentiment analysis pipeline."""
    # Load FinBERT model and tokenizer from Hugging Face
    tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
    model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
    # Create a sentiment analysis pipeline
    nlp = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)
    return nlp

def classify_headlines(nlp_pipeline, headlines: list):
    """Classify a list of headlines into sentiment labels using the provided NLP pipeline.
    Returns a list of labels ('positive', 'neutral', 'negative')."""
    if not headlines:
        return []
    # Use the HuggingFace pipeline to get sentiment
    # The FinBERT model outputs one of three labels for each input
    results = nlp_pipeline(headlines)  # this returns a list of dicts like {'label': 'positive', 'score': 0.98}
    labels = []
    for res in results:
        # The model's labels might be 'positive', 'negative', 'neutral'
        label = res.get('label', '')
        # Normalize label text (in case it's all caps or different format)
        label = label.lower()
        # FinBERT might output labels like 'Positive' or 'NEGATIVE'; we make them uniform
        if label.startswith("neg"):
            labels.append("negative")
        elif label.startswith("pos"):
            labels.append("positive")
        else:
            labels.append("neutral")
    return labels
