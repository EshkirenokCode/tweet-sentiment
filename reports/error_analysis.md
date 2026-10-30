# Error sample — v1.2.0

18 errors sampled with NumPy seed 42, without replacement, sorted by zero-based
test index. IDs and labels are in `test_metrics_error_sample.json`. Observations
are paraphrased; tweet texts are not redistributed. No retuning followed this sample.

| Index | Gold → predicted | Observation |
|---:|---|---|
| 968 | neutral → negative | A headline mentioning riots is treated as the author's negative opinion. |
| 999 | negative → neutral | A statement about unequal justice implies criticism without a direct sentiment adjective. |
| 1078 | negative → neutral | A short sports remark uses identity language as an apparent insult; context is missing. |
| 1479 | negative → neutral | Mockery depends on knowledge of athletes and an unusual description. |
| 2406 | negative → neutral | A disturbing news headline carries implicit condemnation. |
| 5215 | negative → neutral | A two-word political accusation provides little context. |
| 5286 | neutral → negative | A rhetorical geopolitical question looks critical, while gold is neutral. |
| 6221 | negative → neutral | Reported labels and implied disagreement need conversational context. |
| 6373 | neutral → negative | A post announcing a political article contains charged language about its topic. |
| 7943 | negative → neutral | A news-style headline conveys negative political judgment indirectly. |
| 8471 | neutral → negative | A list of tags and topic words contains little interpretable sentiment. |
| 8749 | positive → neutral | A policy suggestion expresses approval through expected health benefits. |
| 8962 | negative → positive | Favorable words about winning and group identity appear inside broader criticism. |
| 9297 | neutral → negative | A claim about election interference is assigned sentiment rather than read as a report. |
| 9414 | negative → neutral | A group-directed question and community announcement have ambiguous tone in isolation. |
| 9594 | negative → neutral | A confrontational purchase recommendation has negative tone. |
| 10425 | neutral → negative | An apology and self-deprecating political reference trigger a negative label. |
| 11960 | neutral → positive | Positive sports achievements appear in a comparison without clear author approval. |

The remaining errors often concern whose sentiment is being classified: a headline,
a quoted stance, the topic, or the author. Sarcasm, mixed cues and missing context
still matter. Some neutral labels are debatable from the isolated text. This random
sample contains no emoji; token retention is covered by separate preprocessing tests.
