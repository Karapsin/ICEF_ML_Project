from model_utils import *
from model_classes import *

def get_PCA_groups(X, patterns):
    """
    pca_groups example:
    pca_groups = {
        'pca1': {'cols': ['col1', 'col2'], 'components': 1},  
        'pca2': {'cols': ['col4', 'col8'], 'components': 2}, 
        }
    """
    output = dict()
    if isinstance(patterns, list): 
        for single_pattern, components in patterns:
            output[single_pattern] = {'cols': get_cols_with_pattern(X, single_pattern), 'components': components}
    else:
        output[patterns[0]] = {"cols": X.columns.to_list(), "components": patterns[1]}

    return output

def get_model_pipeline(X, 
                       model, 
                       poly_features = None,
                       standartize = False,
                       pca_groups = None, 
                       feature_selection = (None, None),
                       return_preproc = False
    ):

    transformers = list()
    extra_tuples_list = list()

    if standartize:
        standardized_pipeline = Pipeline([('scaler', StandardScaler())])
        transformers.append(('standardize_all', standardized_pipeline, X.columns.to_list()))

    # PCA 
    if pca_groups is not None: 
        
        # col names
        pca_features = sum([x[1]['cols'] for x in pca_groups.items()], [])
        other_features = [col for col in X.columns if col not in pca_features]

        # group wise PCA
        pca_objects = {}
        for name, inner_dict in pca_groups.items():
            cols, components = inner_dict['cols'], inner_dict['components']
            pca_instance = PCA(n_components=components)
            pca_pipeline = Pipeline([
                (f'scaler_{name}', StandardScaler()),  
                (f'pca_{name}', pca_instance)  
            ])
            transformers.append((f'pca_{name}', pca_pipeline, cols))
            pca_objects[name] = (pca_instance, cols)

        #PCA perfomance
        for name, (pca_instance, cols) in pca_objects.items():
            X_subset = X[cols]
            X_subset_scaled = StandardScaler().fit_transform(X_subset)
            pca_instance.fit(X_subset_scaled)
            
            explained_variance = pca_instance.explained_variance_ratio_
            cumulative_variance = explained_variance.cumsum()
            print(f"{name}: Explained Variance Ratio per Component: {explained_variance}")
            print(f"{name}: Cumulative Explained Variance: {cumulative_variance[-1]:.4f}")

        # Add passthrough for remaining features
        transformers.append(('passthrough_other', 'passthrough', other_features))

    # Build preprocessor with initial transformers
    if len(transformers) == 0:
        transformers = [('passthrough', 'passthrough', X.columns.to_list())]

    preprocessor = ColumnTransformer(transformers, remainder='drop')

    # poly Features
    if poly_features is not None:
        if standartize:
            poly_pipeline = Pipeline([
                ('polynomial_features', PolynomialFeatures(degree=poly_features, include_bias=False)),
                ('scaler', StandardScaler())
            ])
        else:
            poly_pipeline = Pipeline([
                ('polynomial_features', PolynomialFeatures(degree=poly_features, include_bias=False))
            ])

        # Add polynomial feature transformation as an additional operation
        extra_tuples_list.append(('poly_and_scale', poly_pipeline))

    # feature selection 
    if feature_selection[0] is not None:
        if feature_selection[0] == 'k_best':
            extra_tuples_list.append(('select_k_best', SelectKBest(score_func = f_regression, k = feature_selection[1])))

        elif feature_selection[0] == 'n_best_fits':
            feature_selector = NBestFeaturesSelector(model = model, n_features = feature_selection[1])
            extra_tuples_list.append(('select_n_best', feature_selector))

            model_selector = BestModelSelector(model=model, scoring='neg_mean_absolute_error')
            extra_tuples_list.append(('select_best_model', model_selector))


    pipeline_list = [('preprocessor3', preprocessor)]
    pipeline_list.extend(extra_tuples_list)
    pipeline_list.append(('model', model))

    # final pipeline
    model_pipeline = Pipeline(pipeline_list)

    return model_pipeline if not(return_preproc) else pipeline_list
