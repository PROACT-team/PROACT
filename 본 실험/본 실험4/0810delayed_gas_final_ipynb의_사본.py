# -*- coding: utf-8 -*-
"""0810Delayed gas final.ipynb의 사본

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1Hqw8YvkeWcB7ajwdqkpkA31_XmVrdRoF
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

"""### Preprocessing"""

#현지용
feature = pd.read_csv('/content/drive/MyDrive/Colab Notebooks/본 실험/PACTALS/dataset/0815/0817_X_imputed.csv') 
optimal_gastro = pd.read_csv('/content/drive/MyDrive/Colab Notebooks/본 실험/PACTALS/dataset/0815/0817_optimal_target.csv') 
real_gastro = pd.read_csv('/content/drive/MyDrive/Colab Notebooks/본 실험/PACTALS/dataset/0725/real-target.csv의 사본') 
surv = pd.read_csv('/content/drive/MyDrive/Colab Notebooks/본 실험/survival.csv')

#원준용
from google.colab import files 
uploaded = files.upload()

#원준용
import io
feature = pd.read_csv(io.BytesIO(uploaded['0817_X_imputed.csv'])) 
optimal_gastro = pd.read_csv(io.BytesIO(uploaded['0817_optimal_target.csv'])) 
real_gastro = pd.read_csv(io.BytesIO(uploaded['0817_real-target.csv']))
surv =  pd.read_csv(io.BytesIO(uploaded['survival.csv']))

optimal_gastro.drop(columns='Unnamed: 0', inplace=True)
real_gastro.drop(columns='Unnamed: 0', inplace=True)
feature.drop(columns='Unnamed: 0', inplace=True)

feature.drop(columns='onset_site', inplace=True)
feature['mean_Q1_2_3_mouth'] = feature['mean_Q1_Speech'] + feature['mean_Q2_Salivation'] + feature['mean_Q3_Swallowing']

pip install lifelines

print("There are",len(feature),"patients with feature")
print("There are",len(optimal_gastro),"patients with opt-gas value")
print("There are",len(real_gastro),"patients with real-gas value")
feature_real = feature.merge(real_gastro, on='SubjectID', how='inner')
print("There are",len(feature_real),"patients with feature & real value 1:",len(feature_real[feature_real['status_real']==1]),"0:", len(feature_real[feature_real['status_real']==0]))

# cph_median 출력용 학습 데이터 생성 (onset delta 뺀 것 주의)
feature_opt = feature.merge(optimal_gastro, on='SubjectID', how='inner')
feature_opt.query('time_opt !=0', inplace=True)

df_train = feature_opt.copy()
df_train = df_train[['Age', 'onset_delta', 'fvc_mean',  'mean_Q1_2_3_mouth', 'mean_Q7_Turning_in_Bed', 'slope_Q1_Speech',
                       'slope_Q3_Swallowing', 'weight_slope', 'time_opt', 'status_opt']]
df_train

# cph_median 출력용 투입 데이터 생성
df_train2 = feature_real[['Age', 'onset_delta', 'fvc_mean',  'mean_Q1_2_3_mouth', 'mean_Q7_Turning_in_Bed', 'slope_Q1_Speech',
                       'slope_Q3_Swallowing', 'weight_slope']]
df_train2

from lifelines import CoxPHFitter
cph = CoxPHFitter(penalizer=0.1, l1_ratio=0.2)
cph.fit(df_train, 'time_opt', event_col='status_opt')

cph_median = pd.concat([feature_real['SubjectID'],cph.predict_median(df_train2)], axis=1)
cph_median.columns = ['SubjectID', 'predicted_opt']
cph_median_without_inf = cph_median[cph_median['predicted_opt']!=np.inf]
feat_real_optpred = feature_real.merge(cph_median_without_inf, on='SubjectID', how='inner')
feat_real_optpred['delayed_gas'] = feat_real_optpred['time_real']-feat_real_optpred['predicted_opt']
print('There are ', len(cph_median[cph_median['predicted_opt']==np.inf]), 'inf values which have been removed')
print(cph_median_without_inf)

feat_real_optpred = feature_real.merge(cph_median_without_inf, on='SubjectID', how='inner')
feat_real_optpred['delayed_gas'] = feat_real_optpred['time_real']-feat_real_optpred['predicted_opt']
feat_real_optpred

feat_dg_surv = feat_real_optpred.merge(surv, on='SubjectID', how='inner')
feat_dg_surv

feat_dg_surv

"""# Analysis on Survival effect of delayed gastrostomy"""

feat_dg_surv_filtered = feat_dg_surv[feat_dg_surv['predicted_opt']<feat_dg_surv['time_event']]
print(len(feat_dg_surv_filtered), 'are left, while', len(feat_dg_surv)-len(feat_dg_surv_filtered), "are removed for censoring")

plt.figure(figsize=(8, 3))
sns.histplot(feat_dg_surv_filtered['delayed_gas'])

feat_dg_surv_filtered['time_event'] = feat_dg_surv_filtered['time_event'] - feat_dg_surv_filtered['predicted_opt']

"""#### brief observation: 생존시간과 delayed gas의 상관관계"""

scat_df = feat_dg_surv_filtered.query('status==1 and status_real==1')
fig, ax = plt.subplots(figsize=(6,5))
sns.regplot(x=scat_df['delayed_gas'], y=scat_df['time_event'], fit_reg=True) 
plt.xlabel('Delayed_gastrostomy', fontsize=9)
plt.ylabel('Survival time', fontsize=9)
plt.show()

"""### Group estimation by Kaplan-Meier"""

f_d_s_f_real_1 = feat_dg_surv_filtered[feat_dg_surv_filtered['status_real']==1]
print(f_d_s_f_real_1['delayed_gas'].describe())
print('30% quantile', f_d_s_f_real_1.delayed_gas.quantile(0.3))
print('35% quantile', f_d_s_f_real_1.delayed_gas.quantile(0.35))
print('40% quantile', f_d_s_f_real_1.delayed_gas.quantile(0.4))
print('60% quantile', f_d_s_f_real_1.delayed_gas.quantile(0.6))
print('65% quantile', f_d_s_f_real_1.delayed_gas.quantile(0.65))
print('70% quantile', f_d_s_f_real_1.delayed_gas.quantile(0.7))

feature_early= f_d_s_f_real_1[f_d_s_f_real_1['delayed_gas']<= -46]
feature_medium= f_d_s_f_real_1.query('(delayed_gas > -46) and (delayed_gas <= 90)')
feature_late= f_d_s_f_real_1[feat_dg_surv_filtered['delayed_gas']> 90]

early_list= list(feature_early['SubjectID'])
medium_list= list(feature_medium['SubjectID'])
late_list= list(feature_late['SubjectID'])+list(feat_dg_surv_filtered[feat_dg_surv_filtered['status_real']==0].query('delayed_gas >90')['SubjectID'])

surv_early = feat_dg_surv_filtered.query("SubjectID == {0}".format(early_list))
surv_medium = feat_dg_surv_filtered.query("SubjectID == {0}".format(medium_list))
surv_late = feat_dg_surv_filtered.query("SubjectID == {0}".format(late_list))

print("Subjects are categorized  ", len(surv_early), "(25% Early)", len(surv_medium), '(50% Medium)', len(surv_late), '(25+a% Late)')

from lifelines import KaplanMeierFitter
plt.figure(figsize=(8, 6))
kmf = KaplanMeierFitter()

kmf.fit(surv_early["time_event"], surv_early["status"], label="early",alpha=1)
ax_kmf = kmf.plot(linewidth=3)
kmf.fit(surv_medium["time_event"], surv_medium["status"], label="medium",alpha=1)
ax_kmf = kmf.plot(ax=ax_kmf, color='#FFB291',linewidth=3)
kmf.fit(surv_late["time_event"], surv_late["status"], label="late",alpha=1)
ax_kmf = kmf.plot(ax=ax_kmf, linewidth=3)

ax_kmf.set_ylim(0,1.02)
ax_kmf.set_xlim()
ax_kmf.set_xlabel('time (days)', fontsize=11)
ax_kmf.set_ylabel('survival function, $\hat{S}(t)$', fontsize=13)
plt.title('Group estimation by Kaplan-Meier', fontsize=13)
plt.show()
print('The plot above suggests a time-varying effect of delayed gastrostomy for survival event.')

from lifelines.statistics import logrank_test
logrank_test(surv_early["time_event"], surv_late["time_event"], surv_early["status"], surv_late["status"]).p_value

X_cox = f_d_s_f_real_1[['Age', 'onset_delta', 'fvc_mean',  'mean_Q1_2_3_mouth', 'mean_Q7_Turning_in_Bed', 'slope_Q1_Speech',
                       'slope_Q3_Swallowing', 'weight_slope', 'delayed_gas',
       'time_event', 'status']]

X_cox.to_csv('/content/drive/MyDrive/Colab Notebooks/본 실험/PACTALS/dataset/0815/spss.csv')

from lifelines import CoxPHFitter
cph = CoxPHFitter(penalizer=0.01)
cph.fit(X_cox, 'time_event', event_col='status')
cph.check_assumptions(X_cox, p_value_threshold=0.05)

cph.print_summary()

plt.figure(figsize=(5,10))
plt.xlim([-0.5,7.5])
cph.plot(hazard_ratios=True, color='k')

f_d_s_f_real_1.to_csv('/content/drive/MyDrive/Colab Notebooks/본 실험/PACTALS/dataset/0725/(real=1)_file_for_time_dependent_cox.csv')

"""# Analysis on complicated effect of delayed gastrostomy

In this part, the effect of delayed gastrostomy on other target variables is analyzed

### Extracting target slopes on '365 days after'
"""

lab = pd.read_csv('/content/drive/MyDrive/Colab Notebooks/본 실험/PACTALS/raw data/lab.csv')
weight = pd.read_csv('/content/drive/MyDrive/Colab Notebooks/본 실험/PACTALS/raw data/weight.csv')
fvc = pd.read_csv('/content/drive/MyDrive/Colab Notebooks/본 실험/fvc.csv')

weight = weight[['SubjectID','feature_delta', 'weight']]
Uric_Acid = lab[['SubjectID', 'feature_delta', 'Uric Acid']]
fvc = fvc[['SubjectID', 'feature_delta', 'fvc_percent']]

weight.dropna(inplace=True)
Uric_Acid.dropna(inplace=True)
fvc.dropna(inplace=True)

weight = weight.groupby('SubjectID').agg(['first','last'])
Uric_Acid = Uric_Acid.groupby('SubjectID').agg(['first','last'])
fvc = fvc.groupby('SubjectID').agg(['first','last'])

weight=weight[weight[('feature_delta', 'last')]>=365]
Uric_Acid=Uric_Acid[Uric_Acid[('feature_delta', 'last')]>=365]
fvc=fvc[fvc[('feature_delta', 'last')]>=365]

weight=weight[weight[('feature_delta', 'first')]>=0]
Uric_Acid=Uric_Acid[Uric_Acid[('feature_delta', 'first')]>=0]
fvc=fvc[fvc[('feature_delta', 'first')]>=0]

weight['interval'] = weight[('feature_delta', 'last')] - weight[('feature_delta', 'first')]
Uric_Acid['interval'] = Uric_Acid[('feature_delta', 'last')] - Uric_Acid[('feature_delta', 'first')]
fvc['interval'] = fvc[('feature_delta', 'last')] - fvc[('feature_delta', 'first')]

weight['difference'] = weight[('weight', 'last')] - weight[('weight', 'first')]
Uric_Acid['difference'] = Uric_Acid[('Uric Acid', 'last')] - Uric_Acid[('Uric Acid', 'first')]
fvc['difference'] = fvc[('fvc_percent', 'last')] - fvc[('fvc_percent', 'first')]

weight['weight_target_slope'] = weight['difference']/weight['interval']
Uric_Acid['UrAc_target_slope'] = Uric_Acid['difference']/Uric_Acid['interval']
fvc['fvc_target_slope'] = fvc['difference']/fvc['interval']

weight.reset_index(inplace=True)
Uric_Acid.reset_index(inplace=True)
fvc.reset_index(inplace=True)

weight = weight[['SubjectID', 'weight_target_slope']]
Uric_Acid = Uric_Acid[['SubjectID', 'UrAc_target_slope']]
fvc = fvc[['SubjectID', 'fvc_target_slope']]

"""### Applying Linear Model

#### Effect on **weight** loss
"""

feature_real = feat_real_optpred[feat_real_optpred['status_real']==1].query('time_real <= 365')

feature_real_weight = pd.merge(feature_real, weight, on = 'SubjectID')
feature_real_weight.columns = ['SubjectID', 'Age','Gender', 'diag_delta', 'onset_delta', 'diag_minus_onset', 'fvc_slope',   'fvc_mean',
                     'Creatinine_mean',  'Creatinine_slope','alsfrs_total_slope',  'mean_Q1_Speech','mean_Q2_Salivation',  'mean_Q3_Swallowing',
                 'mean_Q4_Handwriting',   'mean_Q5_Cutting','mean_Q6_Dressing_and_Hygiene', 'mean_Q7_Turning_in_Bed','mean_Q8_Walking',  'mean_Q9_Climbing_Stairs',
                'mean_Q10_Respiratory',  'slope_Q1_Speech', 'slope_Q2_Salivation',  'slope_Q3_Swallowing', 'slope_Q4_Handwriting',   'slope_Q5_Cutting',
       'slope_Q6_Dressing_and_Hygiene',  'slope_Q7_Turning_in_Bed','slope_Q8_Walking',  'slope_Q9_Climbing_Stairs', 'slope_Q10_Respiratory',   'weight_slope',
                   'mean_Q1_2_3_mouth',   'time_real','status_real',   'predicted_opt','delayed_gas',   'weight_target_slope']

df_train1 = feature_real_weight.copy()
df_train1 = df_train1[['Age', 'onset_delta', 'fvc_mean', 'Creatinine_slope', 
                     'alsfrs_total_slope',  'mean_Q1_2_3_mouth',   'mean_Q5_Cutting', 'mean_Q7_Turning_in_Bed', 
                       'slope_Q3_Swallowing', 'slope_Q4_Handwriting', 
                      'weight_slope', 'delayed_gas', 'weight_target_slope']]

colormap = plt.cm.RdBu
plt.figure(figsize=(15,5))
plt.title('Pearson Correlation between Features', y=1.05, size=15)
sns.heatmap(df_train1.astype(float).corr(), linewidths=0.1, vmax=1.0,
	square=True, cmap=colormap, linecolor='white', annot=True, annot_kws={"size":8})

X_train1 = df_train1.drop(columns ='weight_target_slope')
y_train1 = df_train1[['weight_target_slope']]

from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
scaler.fit(X_train1)
X_scaled1 = scaler.transform(X_train1)
X_train1 = pd.DataFrame(X_scaled1, index=X_train1.index, columns=X_train1.columns)

from sklearn.linear_model import LinearRegression
reg = LinearRegression().fit(X_train1, y_train1)

cdf = pd.DataFrame(np.transpose(reg.coef_), X_train1.columns, columns=['Coefficients'])
print(cdf)

import statsmodels.api as sm
x_train1 = sm.add_constant(X_train1,has_constant="add")

model = sm.OLS(y_train1,x_train1)
fitted_model_lr2 = model.fit()

fitted_model_lr2.summary()

from xgboost import XGBRegressor
model_xgb = XGBRegressor()
model_xgb.fit(X_train1, y_train1)

from sklearn.ensemble import RandomForestRegressor 

model_rf = RandomForestRegressor()
model_rf.fit(X_train1, y_train1)

plt.figure(figsize=(15, 5))
plt.subplot(121)
plt.bar(X_train1.columns, model_xgb.feature_importances_)
plt.xticks(rotation=80)
plt.title('XGBoost')

plt.subplot(122)
plt.bar(X_train1.columns, model_rf.feature_importances_)
plt.xticks(rotation=80)
plt.title('Random forest')
plt.show()

"""#### Effect on **fvc**"""

feature_real_fvc = pd.merge(feature_real, fvc, on = 'SubjectID')
feature_real_fvc.columns = ['SubjectID', 'Age','Gender', 'diag_delta', 'onset_delta', 'diag_minus_onset', 'fvc_slope',   'fvc_mean',
                     'Creatinine_mean',  'Creatinine_slope','alsfrs_total_slope',  'mean_Q1_Speech','mean_Q2_Salivation',  'mean_Q3_Swallowing',
                 'mean_Q4_Handwriting',   'mean_Q5_Cutting','mean_Q6_Dressing_and_Hygiene', 'mean_Q7_Turning_in_Bed','mean_Q8_Walking',  'mean_Q9_Climbing_Stairs',
                'mean_Q10_Respiratory',  'slope_Q1_Speech', 'slope_Q2_Salivation',  'slope_Q3_Swallowing', 'slope_Q4_Handwriting',   'slope_Q5_Cutting',
       'slope_Q6_Dressing_and_Hygiene',  'slope_Q7_Turning_in_Bed','slope_Q8_Walking',  'slope_Q9_Climbing_Stairs', 'slope_Q10_Respiratory',   'weight_slope',
                   'mean_Q1_2_3_mouth',   'time_real','status_real',   'predicted_opt','delayed_gas',   'fvc_target_slope']
df_train2 = feature_real_fvc.copy()
df_train2['mean_Q1_2_3_mouth'] = df_train2['mean_Q1_Speech'] + df_train2['mean_Q2_Salivation'] + df_train2['mean_Q3_Swallowing']
df_train2 = df_train2[['Age', 'onset_delta','fvc_mean', 'Creatinine_slope', 
                     'alsfrs_total_slope',  'mean_Q1_2_3_mouth',   'mean_Q5_Cutting', 'mean_Q7_Turning_in_Bed', 
                       'slope_Q3_Swallowing', 'slope_Q4_Handwriting', 
                      'weight_slope', 'delayed_gas', 'fvc_target_slope']]

colormap = plt.cm.RdBu
plt.figure(figsize=(5,5))
plt.title('Pearson Correlation between Features', y=1.05, size=15)
sns.heatmap(df_train2.astype(float).corr(), linewidths=0.1, vmax=1.0,
	square=True, cmap=colormap, linecolor='white', annot=True, annot_kws={"size":8})

X_train2 = df_train2.drop(columns ='fvc_target_slope')
y_train2 = df_train2[['fvc_target_slope']]

from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
scaler.fit(X_train2)
X_scaled2 = scaler.transform(X_train2)
X_train2 = pd.DataFrame(X_scaled2, index=X_train2.index, columns=X_train2.columns)

import statsmodels.api as sm
x_train2 = sm.add_constant(X_train2,has_constant="add")

model = sm.OLS(y_train2,x_train2)
fitted_model_lr2 = model.fit()

fitted_model_lr2.summary()

from xgboost import XGBRegressor
model_xgb = XGBRegressor()
model_xgb.fit(X_train2, y_train2)

from sklearn.ensemble import RandomForestRegressor 

model_rf = RandomForestRegressor()
model_rf.fit(X_train2, y_train2)

plt.figure(figsize=(15, 5))
plt.subplot(121)
plt.bar(X_train2.columns, model_xgb.feature_importances_)
plt.xticks(rotation=80)
plt.title('XGBoost')

plt.subplot(122)
plt.bar(X_train2.columns, model_rf.feature_importances_)
plt.xticks(rotation=80)
plt.title('Random forest')
plt.show()

"""#### Effect on **Uric acid**"""

feature_real_uricacid = pd.merge(feature_real, Uric_Acid, on = 'SubjectID')
feature_real_uricacid.columns = ['SubjectID', 'Age','Gender', 'diag_delta', 'onset_delta', 'diag_minus_onset', 'fvc_slope',   'fvc_mean',
                     'Creatinine_mean',  'Creatinine_slope','alsfrs_total_slope',  'mean_Q1_Speech','mean_Q2_Salivation',  'mean_Q3_Swallowing',
                 'mean_Q4_Handwriting',   'mean_Q5_Cutting','mean_Q6_Dressing_and_Hygiene', 'mean_Q7_Turning_in_Bed','mean_Q8_Walking',  'mean_Q9_Climbing_Stairs',
                'mean_Q10_Respiratory',  'slope_Q1_Speech', 'slope_Q2_Salivation',  'slope_Q3_Swallowing', 'slope_Q4_Handwriting',   'slope_Q5_Cutting',
       'slope_Q6_Dressing_and_Hygiene',  'slope_Q7_Turning_in_Bed','slope_Q8_Walking',  'slope_Q9_Climbing_Stairs', 'slope_Q10_Respiratory',   'weight_slope',
                   'mean_Q1_2_3_mouth',   'time_real','status_real',   'predicted_opt','delayed_gas',   'UrAc_target_slope']
df_train3 = feature_real_uricacid.copy()
df_train3['mean_Q1_2_3_mouth'] = df_train3['mean_Q1_Speech'] + df_train3['mean_Q2_Salivation'] + df_train3['mean_Q3_Swallowing']
df_train3 = df_train3[['Age', 'onset_delta', 'fvc_mean', 'Creatinine_slope', 
                     'alsfrs_total_slope',  'mean_Q1_2_3_mouth',   'mean_Q5_Cutting', 'mean_Q7_Turning_in_Bed', 
                       'slope_Q3_Swallowing', 'slope_Q4_Handwriting', 
                      'weight_slope', 'delayed_gas', 'UrAc_target_slope']]

colormap = plt.cm.RdBu
plt.figure(figsize=(5, 5))
plt.title('Pearson Correlation between Features', y=1.05, size=15)
sns.heatmap(df_train3.astype(float).corr(), linewidths=0.1, vmax=1.0,
	square=True, cmap=colormap, linecolor='white', annot=True, annot_kws={"size":8})

X_train3 = df_train3.drop(columns ='UrAc_target_slope')
y_train3 = df_train3[['UrAc_target_slope']]

from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
scaler.fit(X_train3)
X_scaled3 = scaler.transform(X_train3)
X_train3 = pd.DataFrame(X_scaled3, index=X_train3.index, columns=X_train3.columns)

import statsmodels.api as sm
x_train3 = sm.add_constant(X_train3,has_constant="add")

model = sm.OLS(y_train3,x_train3)
fitted_model_lr2 = model.fit()

fitted_model_lr2.summary()

from xgboost import XGBRegressor
model_xgb = XGBRegressor()
model_xgb.fit(X_train3, y_train3)

from sklearn.ensemble import RandomForestRegressor 

model_rf = RandomForestRegressor()
model_rf.fit(X_train3, y_train3)

plt.figure(figsize=(15, 5))
plt.subplot(121)
plt.bar(X_train3.columns, model_xgb.feature_importances_)
plt.xticks(rotation=80)
plt.title('XGBoost')

plt.subplot(122)
plt.bar(X_train3.columns, model_rf.feature_importances_)
plt.xticks(rotation=80)
plt.title('Random forest')
plt.show()

