# Error sample — v1.2.0

18 Linux x86-64 serving-model errors sampled with NumPy seed 42, without
replacement, sorted by zero-based test index. IDs and labels are in
`test_metrics_error_sample.json`. Observations are paraphrased; tweet texts are
not redistributed. No retuning followed this sample.

| Index | Gold → predicted | Observation |
|---:|---|---|
| 952 | neutral → positive | An emphatic ranking of TV characters is assigned positive sentiment. |
| 985 | negative → neutral | Criticism of unequal pension benefits is expressed as a factual claim. |
| 1045 | positive → neutral | Praise for two athletes' importance to their team is missed. |
| 1460 | positive → neutral | A fashion post with approving slang and a heart emoji is read as neutral. |
| 2373 | neutral → negative | An instruction about voter records is assigned negative sentiment. |
| 5185 | negative → neutral | A request for a politician to support protesters implies dissatisfaction. |
| 5258 | positive → neutral | A motivational message is missed amid tags and a malformed URL boundary. |
| 6198 | positive → neutral | Sharing a musical performance carries no explicit praise in the isolated text. |
| 6362 | positive → neutral | A remark about aspiring to be a political leader has ambiguous tone. |
| 7901 | neutral → negative | A political fundraising headline includes an insult and charged framing. |
| 8445 | negative → neutral | An age-related joke depends on implied mockery. |
| 8699 | positive → neutral | A viewing-progress update has little explicit sentiment despite positive gold. |
| 8908 | neutral → negative | A report about a shop fire is read as the author's negative opinion. |
| 9281 | positive → neutral | A political joke depends on knowing a speechwriter controversy. |
| 9400 | negative → neutral | A short complaint about a joke's emotional effect is missed. |
| 9567 | neutral → negative | A counterfactual political claim uses strongly critical language. |
| 10402 | negative → neutral | A questioning medical-policy headline implies criticism without a direct adjective. |
| 11938 | positive → neutral | A brief movie assessment offers mild approval with sparse context. |

The errors include implicit praise and criticism, quoted or reported sentiment,
sarcasm, slang, and missing context. Some gold labels are debatable from isolated
text. Retaining an emoji in preprocessing does not guarantee the pretrained
WordPiece tokenizer understands it. The sample is descriptive, not a new test set.
