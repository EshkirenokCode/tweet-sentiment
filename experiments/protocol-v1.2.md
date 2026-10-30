# v1.2 candidate protocol

2026-10-30. Keep the pinned TweetEval splits, preprocessing v2 and seed 42.
Fit train only; select by official validation macro-F1. Do not evaluate any new
candidate on test until validation selection is complete. The official test has
already been inspected in previous versions; any final result is a repeat measurement.

Compare eight sparse candidates: word NB-SVM with/without stop words at C=1/4;
word+character NB-SVM keeping stop words at C=1/4; balanced word+character
LinearSVC at C=0.1; balanced word+character logistic regression at C=4.
Use sublinear word/character TF-IDF, word (1,2), min_df=2, max_features=150000;
character (3,5), min_df=3, max_features=150000. One thread per fit.

NB-SVM fits an independent binary log-count ratio for each OvR classifier on train
only, then logistic regression. Compare the best validation result with v1.1.
If sparse models remain weak, add a separately documented pretrained-feature
experiment before any new test evaluation. Keep the deployed v1.1 artifact intact.

Pretrained-feature comparison (declared before encoding or fitting):
`sentence-transformers/all-MiniLM-L6-v2`, revision
`1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, published ONNX int8 ARM64 weights,
mean attention-mask pooling and L2 normalization. The encoder remains frozen.
It is a general sentence-pair encoder, not a TweetEval-finetuned sentiment model.
Use shared preprocessing v2 without stop word removal. Compare six classifiers:
embedding-only logistic regression C=1/10/100; hybrid word+char TF-IDF plus
embedding LinearSVC C=0.1/1 without class weights and C=0.1 balanced. All train-only.
CPU execution; no test encoding/evaluation until selection across both families.

Task fine-tuning (declared after frozen-feature validation, before loading test):
the generic MiniLM encoder above improved validation only modestly. Fine-tune its
BERT sequence-classification form on train for exactly two epochs, batch 32,
AdamW lr=3e-5, weight_decay=0.01, linear schedule with 10% warmup, gradient norm 1,
seed 42, four local CPU threads, no GPU. Keep stop words, shared preprocessing v2.
Select epoch 1 or 2 by validation macro-F1. No extra search or test-driven retries.
Export the selected checkpoint to ONNX and quantize weights to int8; select the
serving precision using validation only, then compare against the frozen/sparse
candidates. Test is still not encoded or evaluated at this stage.

Serving precision rule: prefer int8 if validation macro-F1 is within 0.005 of the
float export. Otherwise retain float only if the 512-MiB serving budget passes;
do not select precision from test results. The service keeps one CPU and its
existing request limits. Serialize ONNX calls to bound peak request memory.

Use batch-one scoring for the final float/int8 validation comparison and all final
test predictions, matching single-request serving. Dynamic int8 activation ranges
can depend on the batch, so do not substitute batch-64 metrics for this decision.
