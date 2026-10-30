# Error sample — v1.1.0

18 errors sampled without replacement using NumPy seed 42, sorted by zero-based
test index. Selection code is in `evaluate.py`; IDs and labels are saved in
`test_metrics_error_sample.json`. Observations are paraphrased to avoid republishing
tweet text. No model changes followed this inspection.

| Index | Gold → predicted | Observation |
|---:|---|---|
| 1028 | negative → neutral | Conditional acceptance of a political appointment is sarcastic criticism. |
| 1076 | negative → neutral | A charged claim about an organization is read as factual text; stance depends on target and context. |
| 1145 | neutral → positive | A short phrase naming a politician provides little sentiment evidence. |
| 1588 | negative → positive | Positive adjectives appear inside an ironic comment about economic policy. |
| 2467 | positive → neutral | Approval of an entertainment program is expressed through slang. |
| 5332 | neutral → positive | A technical announcement includes a favorable superlative. Gold treats the announcement as neutral. |
| 5410 | negative → neutral | Criticism is expressed through contrast and an accusation of selective judgment. |
| 6327 | negative → neutral | Negated effectiveness is followed by a favorable alternative; mixed sentiment. |
| 6462 | neutral → positive | Promotional-looking documentary metadata contains positive surface cues. |
| 8035 | negative → positive | A demand to abolish a political institution has negative stance without a typical negative adjective. |
| 8547 | negative → neutral | Mockery and a negated preference about a politician are missed. |
| 8794 | negative → positive | Uppercase negation and a hostile political hashtag express rejection. |
| 9004 | negative → neutral | A disavowal is followed by an objection; several clauses and negations affect interpretation. |
| 9291 | neutral → positive | An event announcement receives a positive label despite no clear opinion. |
| 9417 | negative → neutral | A cost comparison implies criticism without stating it directly. |
| 9594 | negative → neutral | A confrontational purchase recommendation carries negative tone. |
| 10473 | negative → neutral | A television reference and ironic closing word need context. |
| 11959 | positive → neutral | A sports headline celebrates an award result through domain-specific verbs. |

The sample contains sarcasm, negation, mixed sentiment and political/sports
vocabulary. Some short or announcement-like texts leave the gold label debatable.
There are no emoji examples in this random sample; the preprocessing tests cover
emoji and letter emoticons separately. Eighteen cases do not measure category frequency.

Negative recall remains the weakest part of the classifier. Future model changes
need validation-based selection and a new holdout, or explicit disclosure of test reuse.
