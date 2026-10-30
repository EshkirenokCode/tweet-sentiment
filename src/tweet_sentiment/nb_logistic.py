import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.linear_model import LogisticRegression


class NBLogistic(ClassifierMixin, BaseEstimator):
    """Binary logistic regression on NB log-count-ratio weighted features."""

    def __init__(self, C=1.0):
        self.C = C

    def fit(self, X, y):
        y = np.asarray(y)
        self.classes_ = np.unique(y)
        if len(self.classes_) != 2:
            raise ValueError("NBLogistic requires two classes; use OneVsRestClassifier")
        positive = np.asarray(X[y == self.classes_[1]].sum(axis=0)).ravel() + 1
        negative = np.asarray(X[y == self.classes_[0]].sum(axis=0)).ravel() + 1
        self.ratio_ = np.log(positive / positive.sum()) - np.log(negative / negative.sum())
        self.classifier_ = LogisticRegression(
            C=self.C, solver="liblinear", max_iter=1000, random_state=42
        ).fit(X.multiply(self.ratio_), y)
        self.n_features_in_ = X.shape[1]
        return self

    def decision_function(self, X):
        return self.classifier_.decision_function(X.multiply(self.ratio_))

    def predict(self, X):
        return self.classifier_.predict(X.multiply(self.ratio_))
