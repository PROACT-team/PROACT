Workflow
=========

data imputation.ipynb 
-----------------------
1. Missing data imputation (KNNImputer, IterativeImputer) 
2. Add survival feature (time event & status)
3. Get dummy variable

1st try on cph.ipynb
-----------------------
1. Train/Test set splitting (8:2)
2. Apply CoxPHFitter and print summary 
3. Plot log(HR) value of each feature
4. Predict survival on test data
5. Model Evaluation with 5-fold cross validation
