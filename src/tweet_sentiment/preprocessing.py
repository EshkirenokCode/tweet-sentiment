import html
import re
import unicodedata

from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

NEGATIONS = {"no", "not", "nor", "never"}
STOP_WORDS = frozenset(ENGLISH_STOP_WORDS) - NEGATIONS
TOKEN = re.compile(
    r"[a-z]+(?:'[a-z]+)?|[0-9]+|[!?]+|[:;=8][\-^']?[)(/DPp]|<3|[^\w\s]",
    re.ASCII,
)


def normalize(text: str, remove_stopwords: bool = False) -> str:
    text = unicodedata.normalize("NFKC", html.unescape(text)).lower().replace("’", "'")
    text = re.sub(r"(?:https?://|www\.)\S+", " urltoken ", text)
    text = re.sub(r"(?<!\w)@[\w]+", " usertoken ", text)
    text = text.replace("can't", "can not").replace("won't", "will not")
    text = re.sub(r"n['’]t\b", " not", text)
    text = text.replace("#", "")
    result = []
    for token in TOKEN.findall(text):
        if token.startswith("!"):
            token = "exclaimrepeat" if len(token) > 1 else "exclaim"
        elif token.startswith("?"):
            token = "questionrepeat" if len(token) > 1 else "question"
        elif not (token[0].isalnum() or token == "<3" or len(token) > 1):
            # Retain Unicode symbols (including emoji), discard technical punctuation.
            if not any(unicodedata.category(c).startswith("S") for c in token):
                continue
        if remove_stopwords and token in STOP_WORDS:
            continue
        result.append(token)
    return " ".join(result)


class TextNormalizer(TransformerMixin, BaseEstimator):
    def __init__(self, remove_stopwords=False):
        self.remove_stopwords = remove_stopwords

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return [normalize(text, self.remove_stopwords) for text in X]
