from model_utils import *
class NBestFeaturesSelector(BaseEstimator, TransformerMixin):
    def __init__(self, model, n_features, names_array = None):
        self.model = model
        self.n_features = n_features
        self.selected_features = None
        self.names_array = names_array

    def fit(self, X, y):
        print("initial shape", X.shape)
        scores = {}
        if self.names_array is None:
            self.names_array = np.arange(1, X.shape[1] + 1, 1)

        for idx, feature in enumerate(self.names_array):
            X_feature = pd.DataFrame(X[:, idx], columns=[feature]) if not isinstance(X, pd.DataFrame) else X[[feature]]
            feature_scores = cross_val_score(self.model, X_feature, y, cv=5, scoring='neg_mean_absolute_error')
            scores[feature] = np.mean(feature_scores)

        sorted_features = sorted(scores, key=scores.get, reverse=True)
        self.selected_features = sorted_features[:self.n_features]
        return self

    def transform(self, X):
        if isinstance(X, pd.DataFrame):
            return X[self.selected_features], self.selected_features
        else:
            selected_indices = [list(self.names_array).index(feature) for feature in self.selected_features]
            X_df = pd.DataFrame(X[:, selected_indices])
            X_df.columns = self.selected_features
            return X_df


class BestModelSelector(BaseEstimator):
    def __init__(self, model, scoring='neg_mean_absolute_error', max_features=None):
        self.model = model
        self.scoring = scoring
        self.max_features = max_features
        self.best_model = None
        self.best_score = float('-inf')
        self.best_features = None

    def fit(self, X, y):
        print("final shape", X.shape)
        feature_combinations = get_combs_list(X.columns, upper=self.max_features)

        for comb in feature_combinations:
            X_subset = X[list(comb)]
            cv_scores = cross_val_score(self.model, X_subset, y, cv=5, scoring=self.scoring)
            mean_score = np.mean(cv_scores)


            if mean_score > self.best_score:
                self.best_score = mean_score
                self.best_features = comb
                self.best_model = self.model.fit(X_subset, y)
        return self

    def transform(self, X):
        return X[list(self.best_features)]