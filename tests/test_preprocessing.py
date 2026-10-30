import pytest

from tweet_sentiment.preprocessing import TextNormalizer, normalize


@pytest.mark.parametrize(
    "text, expected",
    [
        ("No, not now; nor ever, never!", {"no", "not", "nor", "never"}),
        ("It isn't good and I can't use it", {"not", "good", "use"}),
        ("He won't go", {"not"}),
        ("I cannot use it", {"not", "use"}),
    ],
)
def test_negations(text, expected):
    assert expected <= set(normalize(text, True).split())


def test_entities_urls_mentions_hashtags():
    assert normalize("@Alice &amp; @Bob https://a.test/x #Great") == (
        "usertoken usertoken urltoken great"
    )
    assert normalize("@other https://b.test") == "usertoken urltoken"


def test_sentiment_signals():
    assert normalize("Wow!!! Really?? :) 😍") == "wow exclaimrepeat really questionrepeat :) 😍"
    assert normalize(":D :-D :P 8)") == ":d :-d :p 8)"


def test_legacy_artifact_state():
    cleaner = TextNormalizer()
    cleaner.__setstate__({"remove_stopwords": True})
    assert cleaner.version == 1
    assert cleaner.transform(["I cannot use it :D"]) == ["use d"]
    assert TextNormalizer(True).transform(["I cannot use it :D"]) == ["not use :d"]


def test_empty_and_stopwords():
    assert normalize(" \t ... # ") == ""
    assert normalize("the and is", True) == ""
    assert normalize("the and is", False) == "the and is"
