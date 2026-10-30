# Model notes

v1.2 fine-tunes a six-layer MiniLM encoder and a new three-class classification
head on TweetEval train. It starts from a general sentence encoder rather than a
checkpoint already fine-tuned for TweetEval sentiment. The source revision and
training parameters are pinned. The final tokenizer and int8 ONNX weights ship
with the service; it never downloads weights during startup or requests.

The original TF-IDF model, NB-weighted logistic models, balanced sparse models,
frozen embeddings and hybrids were compared on validation. The fine-tuned model
won. Stop word removal was tested in sparse baselines; the final encoder keeps
function words and negations for context.

An epoch is one pass through train. Validation selected epoch 2 of exactly two;
it also selected serving precision under a declared 0.005 macro-F1 tolerance.
Int8 reduces weight storage from about 91 MB to 23 MB. Serving uses one CPU thread,
a single-request batch and serialized ONNX calls to bound peak memory.

Macro-F1 averages class F1 equally. Accuracy weights examples equally. The API
returns a label, not calibrated confidence; neural logits are not confidence.
The test set was inspected in earlier releases, so v1.2 metrics are a repeat
measurement. A fresh holdout is needed to assess further model development.
