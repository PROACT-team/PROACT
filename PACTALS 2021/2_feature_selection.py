# -*- coding: utf-8 -*-
"""Feature selection.py

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1iWHxYtMKS2aUzoBrUJ2E_wYh8krdWmg-
"""

# Load packages
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Read datasets needed
from google.colab import files 
uploaded = files.upload()

import io
feature = pd.read_csv(io.BytesIO(uploaded['0817_X_imputed.csv'])) 
target = pd.read_csv(io.BytesIO(uploaded['0817_optimal_target.csv']))   #target means 'time to dietary consistency change'

feature_and_target = pd.merge(feature, target, on = 'SubjectID').drop(columns=['Unnamed: 0_x', 'Unnamed: 0_y'])
feature_and_target

# Check the proportion of censored data
event_distribution = pd.DataFrame(feature_and_target[['status_opt']].value_counts()).reset_index()
event_distribution.columns = ['status', 'count']
event_distribution['status'] = event_distribution['status'].astype('bool')
event_distribution = event_distribution.replace({'status': {False:'0 (censored)', True:'1 (occured)'}})
print(event_distribution)

# Separate 5 subjects for demonstration purpose
df_demonstration = feature_and_target.sample(n=5, random_state = 12)
demonstrationID_list = list(df_demonstration['SubjectID'])

# The other 2558 subjects are used for feature selection
data_for_fitting = feature_and_target[~(feature_and_target['SubjectID'].isin(demonstrationID_list))].drop(columns = 'SubjectID')
y = data_for_fitting[['status_opt']]

from sklearn.model_selection import train_test_split
df_train, df_test, y_train, y_test = train_test_split(data_for_fitting, y, train_size=0.8, test_size=0.2, random_state=11)

print(df_demonstration)
print(df_train)
print(df_test)

"""# 1. Stepwise Selection"""

pip install lifelines

from lifelines import CoxPHFitter
from lifelines.utils import concordance_index

initial_train = df_train.copy()
initial_feature = ['Age', 'Gender', 'diag_delta', 'onset_delta', 'onset_site', 'diag_minus_onset', 'fvc_slope', 'fvc_mean', 'Creatinine_mean',
       'Creatinine_slope', 'alsfrs_total_slope', 'mean_Q1_Speech', 'mean_Q2_Salivation', 'mean_Q3_Swallowing', 'mean_Q4_Handwriting',
       'mean_Q5_Cutting', 'mean_Q6_Dressing_and_Hygiene', 'mean_Q7_Turning_in_Bed', 'mean_Q8_Walking', 'mean_Q9_Climbing_Stairs',
       'mean_Q10_Respiratory', 'slope_Q1_Speech', 'slope_Q2_Salivation', 'slope_Q3_Swallowing', 'slope_Q4_Handwriting', 'slope_Q5_Cutting',
       'slope_Q6_Dressing_and_Hygiene', 'slope_Q7_Turning_in_Bed', 'slope_Q8_Walking', 'slope_Q9_Climbing_Stairs', 'slope_Q10_Respiratory',
       'weight_slope']
SL = 0.05

def cph_forward_stepwise_elimination(initial_train, initial_test, initial_feature, SL_enter, SL_remove):
    
    train = initial_train.copy()
    test = initial_test.copy()
    feature_list = initial_feature.copy()
    selected_feature_list = []

    sv_per_step = []
    adjusted_c_index = []
    steps = []
    step = 0

    while len(feature_list) > 0:
        remainder = list(set(feature_list) - set(selected_feature_list))
        pval = pd.Series(index=remainder)

        for col in remainder:
          X = train[selected_feature_list + [col] + ['time_opt', 'status_opt']]
          cph = CoxPHFitter(penalizer = 0.01)
          cph.fit(X, duration_col='time_opt', event_col='status_opt')
          pval[col] = cph.summary['p'][col]

        min_pval = pval.min()
        if min_pval < SL_enter:
          selected_feature_list.append(pval.idxmin())

          while len(selected_feature_list) > 0:
            selected_X = train[selected_feature_list + ['time_opt', 'status_opt']]
            cph = CoxPHFitter(penalizer = 0.01)
            cph.fit(selected_X, duration_col='time_opt', event_col='status_opt')
            selected_pval = cph.summary['p']
            max_pval = selected_pval.max()
            if max_pval >= SL_remove:
              remove_feature = selected_pval.idxmax()
              selected_feature_list.remove(remove_feature)
            else:
              break

          step += 1
          steps.append(step)
          selected_train = train[selected_feature_list + ['time_opt', 'status_opt']]
          selected_test = test[selected_feature_list + ['time_opt', 'status_opt']]
          cph = CoxPHFitter(penalizer = 0.01)
          cph.fit(selected_train, 'time_opt', event_col='status_opt')
          adj_c_index = concordance_index(selected_test['time_opt'], -cph.predict_partial_hazard(selected_test), selected_test['status_opt'])   
          adjusted_c_index.append(adj_c_index) 
          sv_per_step.append(selected_feature_list.copy())

        else: 
          break

    fig = plt.figure(figsize=(25,10))
    fig.set_facecolor('white')
 
    font_size = 15
    plt.xticks(steps,[f'step {s}\n'+'\n'.join(sv_per_step[i]) for i,s in enumerate(steps)], fontsize=12)
    plt.plot(steps,adjusted_c_index, marker='o')
    
    plt.ylabel('Adjusted C-index',fontsize=font_size)
    plt.grid(True)
    plt.show()

    return selected_feature_list

cph_stepwise_selected_feature = cph_forward_stepwise_elimination(initial_train, df_test,initial_feature, 0.05, 0.05)

# Selection results
cph_stepwise_selected_feature

"""# 2. Check multicollinearity"""

colormap = plt.cm.RdBu
plt.figure(figsize=(9, 7))
plt.title('Pearson Correlation between Features', y=1.05, size=12)
sns.heatmap(feature_and_target.drop(columns = ['time_opt', 'status_opt']).astype(float).corr(), linewidths=0.1, vmax=1.0,
   square=True, cmap=colormap, linecolor='white', annot=False)
# 'onset_site' highly related to 'mean_Q1~Q3'
# 'diag_delta' highly related to 'onset_delta'

"""# 3. Finalize feature selection

### Add or remove some features, based in features chosen by stepwise selection
"""

# Remove 'diag delta'
# Add a meta feature 'mean_Q1_2_3_mouth'
feature['mean_Q1_2_3_mouth'] = feature['mean_Q1_Speech'] + feature['mean_Q2_Salivation'] + feature['mean_Q3_Swallowing']
# Remove 'onset site', 'mean_Q1_Speech','mean_Q2_Salivation', 'mean_Q3_Swallowing'

# Final list
feature_list = ['Age', 'onset_delta', 'fvc_mean', 'Creatinine_mean', 'mean_Q1_2_3_mouth', 'mean_Q5_Cutting', 
                'mean_Q7_Turning_in_Bed', 'slope_Q1_Speech', 'slope_Q3_Swallowing', 'weight_slope']
feature_list
