# Data provenance and conditions

The source is the sentiment task of [TweetEval](https://github.com/cardiffnlp/tweeteval),
derived from [SemEval-2017 Task 4](https://aclanthology.org/S17-2088/).
The downloader uses the official plain-text files at commit
`4fbd22cd78421f05b1ecdb4fc5725bc7a7bd8f66`, not an executable dataset script.
`reports/data_manifest.json` records URLs, SHA-256, retrieval time, counts and labels.
Subsequent downloads must match those hashes; training verifies every file again.

Checked on 2026-10-28:

- [TweetEval's upstream notice](https://github.com/cardiffnlp/tweeteval/tree/4fbd22cd78421f05b1ecdb4fc5725bc7a7bd8f66#license)
  says individual task and Twitter restrictions can apply.
- [The Hugging Face dataset card](https://huggingface.co/datasets/cardiffnlp/tweet_eval)
  lists the license as `unknown`.
- [The SemEval full-data download page](https://alt.qcri.org/semeval2017/task4/index.php?id=download-the-full-training-data-for-semeval-2017-task-4)
  asks recipients to maintain Twitter's terms and delete tweets no longer public.
  A clear standalone license granting unrestricted redistribution was not established.

This repository therefore does not redistribute tweet texts or claim a license for
the corpus. The ignored `data/` directory is for local reproduction. Error analysis
uses split indices and paraphrased observations. API examples are original sentences.
The trained linear model contains a vocabulary of n-grams and coefficients, not a
copy of the full corpus; its availability does not grant rights to source tweets.
Review source conditions before other uses or redistribution.

References: Barbieri et al. (2020), *TweetEval: Unified Benchmark and Comparative
Evaluation for Tweet Classification*, Findings of EMNLP;
Rosenthal, Farra and Nakov (2017), *SemEval-2017 Task 4: Sentiment Analysis in Twitter*.
