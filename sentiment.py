
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline

# Cache the model loading so it doesn't re-run on every interaction

def load_sentiment_model():
    # Load FinBERT model and tokenizer from Hugging Face
    tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
    model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")


    # analysis pipeline
    nlp = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)
    return nlp



def classify_headlines(nlp_pipeline, headlines: list):
    """Classify a list of headlines into sentiment labels using the provided NLP pipeline. Returns a list of labels ('positive', 'neutral', 'negative')."""
    if not headlines:
        return []



    # Use the HuggingFace pipeline to get sentiment
    # The FinBERT model outputs one of three labels for each input
    results = nlp_pipeline(headlines)  # this returns a list of dicts like {'label': 'positive', 'score': 0.98}
    labels = []




    for res in results:
        # The model's labels might be 'positive', 'negative', 'neutral'
        label = res.get('label', '')

        # Simple Case Stuff
        label = label.lower()


        # FinBERT labels are either 'Positive' or 'NEGATIVE'
        if label.startswith("neg"):
            labels.append("negative")
        elif label.startswith("pos"):
            labels.append("positive")
        else:
            labels.append("neutral")
    return labels
