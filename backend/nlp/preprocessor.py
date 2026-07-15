import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

# Download required NLTK data (idempotent)
for resource in ["punkt", "punkt_tab", "stopwords"]:
    nltk.download(resource, quiet=True)

_stemmer = PorterStemmer()
_stop_words = set(stopwords.words("english")) - {
    "what",
    "how",
    "why",
    "which",
    "where",
    "when",
    "who",
    "not",
    "no",
}


def preprocess(text: str) -> str:
    """Lowercase, tokenize, remove stopwords, stem."""
    if not text or not text.strip():
        return ""
    text = text.lower().strip()
    # Replace hyphens/underscores with spaces so compound terms tokenize correctly
    # e.g. "object-oriented" -> "object oriented", not "objectoriented"
    text = re.sub(r"[-_]", " ", text)
    text = re.sub(r"[^a-z0-9\s]", "", text)
    tokens = word_tokenize(text)
    tokens = [_stemmer.stem(t) for t in tokens if t not in _stop_words and len(t) > 1]
    return " ".join(tokens)
