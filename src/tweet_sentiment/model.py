from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.svm import LinearSVC

from tweet_sentiment.preprocessing import TextNormalizer


def build_model(candidate, config):
    word = TfidfVectorizer(
        tokenizer=str.split,
        token_pattern=None,
        lowercase=False,
        ngram_range=tuple(config["word_ngram_range"]),
        min_df=config["word_min_df"],
        max_features=config["word_max_features"],
        sublinear_tf=config["sublinear_tf"],
    )
    features = word
    if candidate["char"]:
        char = TfidfVectorizer(
            analyzer="char",
            lowercase=False,
            ngram_range=tuple(config["char_ngram_range"]),
            min_df=config["char_min_df"],
            max_features=config["char_max_features"],
            sublinear_tf=config["sublinear_tf"],
        )
        features = FeatureUnion([("word", word), ("char", char)], n_jobs=1)
    kind = candidate["kind"]
    if kind == "dummy":
        classifier = DummyClassifier(strategy="most_frequent", random_state=config["seed"])
    elif kind == "lr":
        classifier = LogisticRegression(
            C=candidate["C"], max_iter=1000, random_state=config["seed"]
        )
    else:
        classifier = LinearSVC(
            C=candidate["C"], dual=True, max_iter=5000, random_state=config["seed"]
        )
    return Pipeline(
        [
            ("normalize", TextNormalizer(candidate["remove_stopwords"])),
            ("tfidf", features),
            ("classifier", classifier),
        ]
    )
