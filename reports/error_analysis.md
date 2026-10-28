# Error analysis

Model: `artifacts/model.joblib`, SHA-256 in `artifacts/metadata.json`.
Sample: 18 errors selected with `numpy.random.default_rng(42).choice` without
replacement from every wrong prediction, then sorted by official zero-based test
index. The IDs and labels are also in `test_metrics_error_sample.json`.
Observations below were made after final evaluation; no retuning followed.
Texts are deliberately not reproduced. Categories are interpretive, not extra gold labels.

| Test index | Gold → predicted | Observation |
|---:|---|---|
| 1042 | neutral → negative | Farewell to a public figure contains sad emoji. Expressed sadness and an annotator's neutral stance are difficult to separate; potentially debatable label. |
| 1078 | negative → neutral | Short sports-related remark uses identity language as an apparent insult; missing conversational context and entity knowledge. |
| 1151 | neutral → positive | Policy statement has an approving emoji. The positive signal is explicit but gold remains neutral; potentially debatable label. |
| 1589 | neutral → negative | Political/security question includes negation and charged domain terms; a question is treated as negative opinion. |
| 2471 | negative → neutral | A reported quotation criticizes a person. The model misses the target and negative stance inside a news-like headline. |
| 5340 | negative → neutral | Political criticism uses a destructive idiom; domain-specific context and figurative language. |
| 5417 | neutral → positive | A social-media challenge caption includes a negated interest statement. Retaining negation alone does not model its scope or gold-neutral framing. |
| 6335 | neutral → positive | Political comment likely mixes humor or irony with positive adjectives; sarcasm is plausible but cannot be established from text alone. |
| 6471 | negative → positive | Strong criticism about social benefits contains surface positive terms. Mixed lexical cues and long-range sentence composition overwhelm the insult. |
| 8034 | neutral → positive | Very short approving phrase addressed to several accounts; gold is debatable without the conversation. |
| 8547 | negative → neutral | Mockery and an explicit negative preference about a politician; negation scope and entity-specific stance are missed. |
| 8794 | negative → positive | Categorical rejection with uppercase negation and an antagonistic political hashtag; retained tokens do not guarantee compositional understanding. |
| 9004 | negative → neutral | Disavowal followed by a belief-based objection; mixed stance and multiple negations require context and scope. |
| 9291 | neutral → positive | Announcement about watching an awards event has no strong sentiment. Learned event/entertainment associations create a false positive. |
| 9417 | negative → neutral | A healthcare cost comparison implies criticism without an explicit sentiment adjective; implied meaning and missing context. |
| 9592 | negative → positive | A proposal to replace a religious leader uses favorable words about the replacement. Target selection and mixed sentiment. |
| 10476 | positive → neutral | Celebratory slang and a reference to a magician express pride; idiom and entity knowledge are missed. |
| 11958 | negative → neutral | Quoted derogatory nickname is presented as reported speech; target, quoted sentiment and pragmatic context are missed. |

Negation appears in several failures despite preservation. This is a limitation
of sparse local n-grams, not a reason to remove negations. Emoji can create a
reasonable surface prediction that disagrees with a neutral gold label. The sample
also suggests political domain vocabulary, sarcasm, mixed sentiment, missing
conversation context and annotation ambiguity. Eighteen errors cannot estimate
the prevalence of these categories across the whole dataset.

The official test has many more negative examples and fewer positive examples
than train. This observed distribution shift and the context-heavy sampled errors
are possible contributors to the validation/test gap, not proof of causation.
Negative recall (0.4434) is the most visible class weakness.

Next experiments would compare class weighting and negation-scope features on
validation or a new development split. A compact pretrained encoder is a later
accuracy/latency tradeoff. Because this test has now been inspected, improvements
must disclose test reuse or use a new untouched holdout.
