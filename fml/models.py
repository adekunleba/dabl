import warnings
import numpy as np
import pandas as pd

from sklearn.model_selection import cross_validate
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.dummy import DummyClassifier
from sklearn.utils.multiclass import type_of_target
from sklearn.preprocessing import MinMaxScaler
from sklearn.naive_bayes import GaussianNB, MultinomialNB
from sklearn.tree import DecisionTreeClassifier
from sklearn.pipeline import make_pipeline
from sklearn.exceptions import UndefinedMetricWarning

from .preprocessing import FriendlyPreprocessor


class FriendlyClassifier(BaseEstimator, ClassifierMixin):
    """Automagic anytime classifier
    """
    def __init__(self):
        pass

    def fit(self, X, y):

        target_type = type_of_target(y)
        if target_type == "binary":
            self.scoring_ = ['accuracy', 'average_precision', 'roc_auc',
                             'precision_macro']
        elif target_type == "multiclass":
            self.scoring_ = ['accuracy', 'precision_macro',
                             'recall_macro']
        else:
            raise ValueError("Unknown target type: {}".format(target_type))
        self.log_ = []
        n_classes = len(np.unique(y))

        # Heuristic: start with fast / instantaneous models
        fast_ests = [DummyClassifier(strategy="prior"),
                     make_pipeline(FriendlyPreprocessor(), GaussianNB()),
                     make_pipeline(FriendlyPreprocessor(scale=False),
                                   MinMaxScaler(), MultinomialNB()),
                     make_pipeline(FriendlyPreprocessor(scale=False),
                                   DecisionTreeClassifier(max_depth=1, class_weight="balanced")),
                     make_pipeline(FriendlyPreprocessor(scale=False),
                                   DecisionTreeClassifier(
                                       max_depth=max(5, n_classes), class_weight="balanced"))
                     ]
        self.current_best_ = -np.inf
        for ests in fast_ests:
            self._evaluate_one(ests, X, y)

    def predict(self, X):
        self.est_.predict(X)

    def _evaluate_one(self, estimator, X, y):
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore',
                                    category=UndefinedMetricWarning)       
            res = cross_validate(estimator, X, y, cv=5, scoring=self.scoring_,
                                 return_train_score=True)
        res_mean = pd.DataFrame(res).mean(axis=0)
        try:
            name = str(estimator.steps[-1][1])
        except AttributeError:
            name = str(estimator)
        # FIXME don't use accuracy for getting the best?
        print(name)
        print(res_mean)
        res_mean.name = name
        self.log_.append(res_mean)