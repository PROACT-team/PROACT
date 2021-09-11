# -*- coding: utf-8 -*-
"""1. Preprocessing 0911

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1gdFMdxhkNk1QmS9kAWEcmbF7vqOxjqoX
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from google.colab import drive
drive.mount('/content/drive')

# import raw data 현지용
demographics = pd.read_csv('/content/drive/MyDrive/Colab Notebooks/본 실험/PACTALS/raw data/demographic.csv')
als_hx = pd.read_csv('/content/drive/MyDrive/Colab Notebooks/본 실험/PACTALS/raw data/als_hx.csv')
alsfrs_total_3mo = pd.read_csv('/content/drive/MyDrive/Colab Notebooks/본 실험/PACTALS/raw data/alsfrs_total_3mo_meta_slope.csv')
fvc_3mo = pd.read_csv('/content/drive/MyDrive/Colab Notebooks/본 실험/PACTALS/raw data/fvc_3mo_meta.csv')
lab = pd.read_csv('/content/drive/MyDrive/Colab Notebooks/본 실험/PACTALS/raw data/lab.csv')
weight = pd.read_csv('/content/drive/MyDrive/Colab Notebooks/본 실험/PACTALS/raw data/weight.csv')
alsfrs_q_raw = pd.read_csv('/content/drive/MyDrive/Colab Notebooks/본 실험/PACTALS/raw data/ALSFRS_original_final.csv')
fvc = pd.read_csv('/content/drive/MyDrive/Colab Notebooks/본 실험/fvc.csv')

# Read datasets needed
from google.colab import files 
uploaded = files.upload()

# import raw data 원준용
import io
demographics = pd.read_csv(io.BytesIO(uploaded['demographic.csv']))
als_hx = pd.read_csv(io.BytesIO(uploaded['als_hx.csv']))
alsfrs_total_3mo = pd.read_csv(io.BytesIO(uploaded['alsfrs_total_3mo_meta_slope.csv']))
fvc_3mo = pd.read_csv(io.BytesIO(uploaded['fvc_3mo_meta.csv']))
lab = pd.read_csv(io.BytesIO(uploaded['lab.csv']))
weight = pd.read_csv(io.BytesIO(uploaded['weight.csv']))
alsfrs_q_raw = pd.read_csv(io.BytesIO(uploaded['ALSFRS_original.csv']))
fvc = pd.read_csv(io.BytesIO(uploaded['fvc.csv']))

"""# 1. Extracting feature variables

## 1-1. Static features

### (1) Age/Gender (Demographics)
"""

demographics = demographics[['SubjectID', 'Age', 'Gender']]

sns.histplot(demographics['Age'])

demographics['Age'].describe() # min = 18, max = 88

# Convert 'Age' into ordered-categorical data (categorize in  5 years)
age_min = 15 

def cat_age(age, age_min):
  return (age - age_min) // 5

demographics['Age'] = demographics.apply(lambda x: cat_age(x['Age'], age_min), axis = 1)
sns.histplot(demographics['Age'])

# Female = 0, Male = 1
Gend = {"F":0, "M":1}
demographics = demographics.replace({'Gender':Gend})
demographics #8653 data

"""### (2) diag_delta/onset_delta/diag_minus_onset/onset_site (ALS history)"""

als_hx = als_hx[['SubjectID', 'diag_delta', 'onset_delta', 'onset_site']]
als_hx['diag_minus_onset'] = als_hx['diag_delta']-als_hx['onset_delta'] #define 'diag_minus_onset' as time difference between onset and diagnosis

# Convert scale 'days' to 'month'
als_hx['diag_delta'] = als_hx['diag_delta']/(365/12)
als_hx['onset_delta'] = als_hx['onset_delta']/(365/12)
als_hx['diag_minus_onset'] = als_hx['diag_minus_onset']/(365/12)

# Bubar_onset = 1, non-Bulbar_onset = 0
onsetsite = {"Other":0, "Bulbar":1, "Limb":0, "Limb and Bulbar":0}
als_hx = als_hx.replace({'onset_site':onsetsite})
als_hx #4454 data

"""## 1-2. Time-resolved features

### (1) alsfrs total slope / FVC
"""

alsfrs_total_slope = alsfrs_total_3mo[['SubjectID', 'alsfrs_total_slope']]
fvc_3mo = fvc_3mo[['SubjectID', 'fvc_slope', 'fvc_mean']]

# Convert scale 'days' to 'month'
alsfrs_total_slope['alsfrs_total_slope'] = alsfrs_total_slope['alsfrs_total_slope']*(365/12)
alsfrs_total_slope #6507 data

# Convert scale 'days' to 'month'
fvc_3mo['fvc_slope'] = fvc_3mo['fvc_slope']*(365/12)
fvc_3mo #7217 data

"""### (2) Creatinine"""

creatinine = lab[['SubjectID', 'feature_delta', 'Creatinine']]

# Check string value
creatinine[creatinine['Creatinine']=='<18'] #There are 2 subjects with string value '<18'

# Remove string value and change into float datatype
creatinine = creatinine[creatinine['Creatinine']!='<18']
creatinine = creatinine.astype('float')
creatinine.dtypes

# Filter first 3 month data
creatinine_3mo = creatinine.query('(feature_delta < 92) and (feature_delta >= 0)')

# Extracting mean_creatinine
mean_creatinine = creatinine_3mo.groupby('SubjectID').agg('mean')
mean_creatinine = mean_creatinine.reset_index()
mean_creatinine.drop(columns='feature_delta', inplace=True)
mean_creatinine #7712 data

# Calculate slope of creatinine
C1 = creatinine_3mo.groupby('SubjectID').agg(['first', 'last'])
C1.reset_index(inplace=True)

C1['interval'] = C1[('feature_delta', 'last')] - C1[('feature_delta', 'first')]  # define time interval in 3mo data
C1 = C1[C1['interval']!=0]  # time interval should be positive

C1['interval'] = C1[('feature_delta', 'last')] - C1[('feature_delta', 'first')]
C1['difference'] = C1[('Creatinine', 'last')] - C1[('Creatinine', 'first')]
C1['Creatinine_slope'] = C1['difference']/ C1['interval']
C1 = C1[['SubjectID', 'interval','Creatinine_slope']]
C1

sns.histplot(x = C1['interval'])

# data with time interval less than 30 days is regarded as missing data
slope_creatinine_short = C1[C1['interval'] <30]
slope_creatinine_long = C1[C1['interval']>=30]
slope_creatinine_short['Creatinine_slope']= np.nan

slope_creatinine = pd.concat([slope_creatinine_long, slope_creatinine_short], axis=0)

slope_creatinine.drop(columns='interval', inplace=True)
slope_creatinine #5945 data

# Convert scale 'days' to 'month'
slope_creatinine['Creatinine_slope'] = slope_creatinine['Creatinine_slope']*(365/12)

# Merge mean_creatinine & slope_creatinine
Creatinine_summary = mean_creatinine.merge(slope_creatinine, on = 'SubjectID', how='inner')
Creatinine_summary.columns = ['SubjectID', 'Creatinine_mean', 'Creatinine_slope']
Creatinine_summary #5945 data

"""### (2) alsfrs_q"""

alsfrs_q_raw1 = alsfrs_q_raw[['SubjectID', 'feature_delta', 'Q1_Speech','Q2_Salivation', 'Q3_Swallowing', 'Q4_Handwriting', 
                             'Q5_Cutting','Q6_Dressing_and_Hygiene', 'Q7_Turning_in_Bed', 'Q8_Walking', 'Q9_Climbing_Stairs', 'Q10_Respiratory']]

# Filter first 3 month data
alsfrs_q_raw_3mo = alsfrs_q_raw1.query('(feature_delta < 92) and (feature_delta >= 0)')

# Extracting mean_alsfrs_q
mean_alsfrs_q = alsfrs_q_raw_3mo.groupby('SubjectID').agg('mean')
mean_alsfrs_q = mean_alsfrs_q.reset_index()
mean_alsfrs_q.drop(columns='feature_delta', inplace=True)
mean_alsfrs_q.columns=['SubjectID', 'mean_Q1_Speech', 'mean_Q2_Salivation', 'mean_Q3_Swallowing', 'mean_Q4_Handwriting', 
            'mean_Q5_Cutting','mean_Q6_Dressing_and_Hygiene', 'mean_Q7_Turning_in_Bed', 'mean_Q8_Walking', 'mean_Q9_Climbing_Stairs', 'mean_Q10_Respiratory']
mean_alsfrs_q #6507 data

#Calculate slope of alsfrs_q
df3 = alsfrs_q_raw_3mo.groupby('SubjectID').agg(['first', 'last'])
df3['interval'] = df3.iloc[:, 1] - df3.iloc[:, 0]
df3 = df3[df3['interval']!=0]

df3['slope_Q1_Speech'] = (df3.iloc[:,3] - df3.iloc[:,2])/df3['interval']
df3['slope_Q2_Salivation'] = (df3.iloc[:,5] - df3.iloc[:,4])/df3['interval']
df3['slope_Q3_Swallowing'] = (df3.iloc[:,7] - df3.iloc[:,6])/df3['interval']
df3['slope_Q4_Handwriting'] = (df3.iloc[:,9] - df3.iloc[:,8])/df3['interval']
df3['slope_Q5_Cutting'] = (df3.iloc[:,11] - df3.iloc[:,10])/df3['interval']
df3['slope_Q6_Dressing_and_Hygiene'] = (df3.iloc[:,13] - df3.iloc[:,12])/df3['interval']
df3['slope_Q7_Turning_in_Bed'] = (df3.iloc[:,15] - df3.iloc[:,14])/df3['interval']
df3['slope_Q8_Walking'] = (df3.iloc[:,17] - df3.iloc[:,16])/df3['interval']
df3['slope_Q9_Climbing_Stairs'] = (df3.iloc[:,19] - df3.iloc[:,18])/df3['interval']
df3['slope_Q10_Respiratory'] = (df3.iloc[:,21] - df3.iloc[:,20])/df3['interval']

df3 = df3.reset_index()
df3 = df3[[(                    'SubjectID',      ''),
            (                     'interval',      ''),
            (              'slope_Q1_Speech',      ''),
            (          'slope_Q2_Salivation',      ''),
            (          'slope_Q3_Swallowing',      ''),
            (         'slope_Q4_Handwriting',      ''),
            (             'slope_Q5_Cutting',      ''),
            ('slope_Q6_Dressing_and_Hygiene',      ''),
            (      'slope_Q7_Turning_in_Bed',      ''),
            (             'slope_Q8_Walking',      ''),
            (     'slope_Q9_Climbing_Stairs',      ''),
            (        'slope_Q10_Respiratory',      '')]]
df3.columns = ['SubjectID', 'interval', 'slope_Q1_Speech', 'slope_Q2_Salivation', 'slope_Q3_Swallowing', 'slope_Q4_Handwriting', 'slope_Q5_Cutting','slope_Q6_Dressing_and_Hygiene','slope_Q7_Turning_in_Bed', 'slope_Q8_Walking', 'slope_Q9_Climbing_Stairs', 'slope_Q10_Respiratory']

# data with time interval less than 30 days is regarded as missing data
slope_alsfrs_q_short = df3[df3['interval'] <30]
slope_alsfrs_q_long = df3[df3['interval']>=30]
slope_alsfrs_q_short[              'slope_Q1_Speech']= np.nan
slope_alsfrs_q_short[          'slope_Q2_Salivation']=np.nan
slope_alsfrs_q_short[          'slope_Q3_Swallowing']=np.nan
slope_alsfrs_q_short[         'slope_Q4_Handwriting']=np.nan
slope_alsfrs_q_short[             'slope_Q5_Cutting']=np.nan
slope_alsfrs_q_short['slope_Q6_Dressing_and_Hygiene']=np.nan
slope_alsfrs_q_short[      'slope_Q7_Turning_in_Bed']=np.nan
slope_alsfrs_q_short[             'slope_Q8_Walking']=np.nan
slope_alsfrs_q_short[     'slope_Q9_Climbing_Stairs']=np.nan
slope_alsfrs_q_short[        'slope_Q10_Respiratory']=np.nan
slope_alsfrs_q = pd.concat([slope_alsfrs_q_long, slope_alsfrs_q_short], axis=0)

slope_alsfrs_q.drop(columns='interval', inplace=True)
slope_alsfrs_q #6167 data

# Convert scale 'days' to 'month'
slope_alsfrs_q['slope_Q1_Speech'] = slope_alsfrs_q['slope_Q1_Speech']*(365/12)
slope_alsfrs_q['slope_Q2_Salivation'] = slope_alsfrs_q['slope_Q2_Salivation']*(365/12)
slope_alsfrs_q['slope_Q3_Swallowing'] = slope_alsfrs_q['slope_Q3_Swallowing']*(365/12)
slope_alsfrs_q['slope_Q4_Handwriting'] = slope_alsfrs_q['slope_Q4_Handwriting']*(365/12)
slope_alsfrs_q['slope_Q5_Cutting'] = slope_alsfrs_q['slope_Q5_Cutting']*(365/12)
slope_alsfrs_q['slope_Q6_Dressing_and_Hygiene'] = slope_alsfrs_q['slope_Q6_Dressing_and_Hygiene']*(365/12)
slope_alsfrs_q['slope_Q7_Turning_in_Bed'] = slope_alsfrs_q['slope_Q7_Turning_in_Bed']*(365/12)
slope_alsfrs_q['slope_Q8_Walking'] = slope_alsfrs_q['slope_Q8_Walking']*(365/12)
slope_alsfrs_q['slope_Q9_Climbing_Stairs'] = slope_alsfrs_q['slope_Q9_Climbing_Stairs']*(365/12)
slope_alsfrs_q['slope_Q10_Respiratory'] = slope_alsfrs_q['slope_Q10_Respiratory']*(365/12)
slope_alsfrs_q

"""### (3) Weight slope"""

# Filter first 3 month data
weight_3mo = weight.query('(feature_delta < 92) and (feature_delta >= 0)')

W1 = weight_3mo.groupby('SubjectID').agg(['first', 'last'])
W1.reset_index(inplace=True)

W1['interval'] = W1[('feature_delta', 'last')] - W1[('feature_delta', 'first')]
W1 = W1[W1['interval']!=0]
W1['difference'] = W1[('weight', 'last')] - W1[('weight', 'first')]

W1['weight_slope'] = W1['difference']/ W1['interval']
W1 = W1[['SubjectID', 'interval', 'weight_slope']]
W1.columns = ['SubjectID','interval','weight_slope']

# data with time interval less than 30 days is regarded as missing data
slope_weight_short = W1[W1['interval'] <30]
slope_weight_long = W1[W1['interval']>=30]

slope_weight_short['weight_slope']=np.nan
weight_slope = pd.concat([slope_weight_short, slope_weight_long], axis=0)
weight_slope.drop(columns='interval', inplace=True)

# Convert scale 'days' to 'month'
weight_slope['weight_slope'] = weight_slope['weight_slope']*(365/12)
weight_slope #5506 data

"""## 1-3. Merging all features"""

features = pd.DataFrame(columns=['SubjectID'])
feature_list = [demographics, als_hx, fvc_3mo, Creatinine_summary, alsfrs_total_slope, mean_alsfrs_q, slope_alsfrs_q, weight_slope]
for i in feature_list :
    df = i
    features = features.merge(df, on='SubjectID', how='outer')
features #9844 data

"""## 1-4. Check NaN proportion """

def report_nulls(df):
    '''
    Show a fast report of the DF.
    '''
    rows = df.shape[0]
    columns = df.shape[1]
    null_cols = 0
    list_of_nulls_cols = []
    list_of_nulls_cols_pcn = []
    list_of_nulls_cols_over60 = []
    for col in list(df.columns):
        null_values_rows = df[col].isnull().sum()
        null_rows_pcn = round(((null_values_rows)/rows)*100, 2)
        col_type = df[col].dtype
        if null_values_rows > 0:
            print("The column {} has {} null values. It is {}% of total rows.".format(col, null_values_rows, null_rows_pcn))
            print("The column {} is of type {}.\n".format(col, col_type))
            null_cols += 1
            list_of_nulls_cols.append(col)
            list_of_nulls_cols_pcn.append(null_rows_pcn)
            if null_rows_pcn > 60:
                list_of_nulls_cols_over60.append(col)
    null_cols_pcn = round((null_cols/columns)*100, 2)
    print("The DataFrame has {} columns with null values. It is {}% of total columns.".format(null_cols, null_cols_pcn))
    plt.plot(list_of_nulls_cols, list_of_nulls_cols_pcn)
    return list_of_nulls_cols_over60

report_nulls(features) # {onset_delta / diag_delta / diag_minus_onset}-> 54.75%  {onset_site}-> 54.76%  {mean_alsfrs_q} -> 33.9%  {slope_alsfrs_q} -> 42.52%  of Total 9844 data

features.isnull().sum()

# Drop NaN of {onset_delta / diag_delta / diag_minus_onset} & {onset_site}
feature_drop_delta = features.dropna(subset=['onset_delta', 'onset_site'])  # patients with NaN value of 'onset_delta' also has NaN value for 'diag_delta' and 'diag_minus_onset'
feature_drop_delta # 4453 data

feature_drop_delta.isnull().sum() # {mean_alsfrs_q} -> 365 NaN values,  {slope_alsfrs_q} -> 1035 NaN values

# Drop NaN of {mean_alsfrs_q} 
feature_drop_delta_mean = feature_drop_delta.dropna(subset=['mean_Q1_Speech'])
feature_drop_delta_mean.isnull().sum()

report_nulls(feature_drop_delta_mean) # {onset_delta / diag_delta / diag_minus_onset}-> 0%  {onset_site}-> 0%  {mean_alsfrs_q} -> 0%  {slope_alsfrs_q} -> 16.39%  of Total 4088 data

feature_drop_delta_mean.to_csv('/content/drive/MyDrive/Colab Notebooks/본 실험/PACTALS/dataset/0725/0815featurewithnans.csv')

"""## 1-5. Data imputation"""

from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer
from sklearn import linear_model

# Data Imputation with IterativeImputer
X = feature_drop_delta_mean
columns = X.columns
imputer = IterativeImputer(sample_posterior = True)
ar = imputer.fit_transform(X)
X_imputed = pd.DataFrame(ar, columns = columns)

X_imputed

X_imputed.to_csv('/content/drive/MyDrive/Colab Notebooks/본 실험/PACTALS/dataset/0815/0817_X_imputed.csv')

"""# 2. Extracting target variables

## 2-1. Optimal target

### (1) Excluding [initial FVC < 50]
"""

fvc_a = fvc.groupby('SubjectID').agg(['first', 'last'])
fvc_a = fvc_a.reset_index()
fvc_a #7312 data

# Remove rows with 'last feature_delta == first feature_delta'
fvc_a = fvc_a[fvc_a[('feature_delta', 'last')]!= fvc_a[('feature_delta', 'first')]]
fvc_a #6073 data

# Select rows with 'first fvc_percent >= 50'
fvc_a = fvc_a[fvc_a[('fvc_percent', 'first')]>=50]
fvc_a = fvc_a.reset_index().drop(columns='index')
fvc_filtered_extent = list(fvc_a['SubjectID'])
len(fvc_filtered_extent) #5755 data

"""### (2) Subtracting [initial Q3 score <=2 ]"""

alsfrs_Sw = alsfrs_q_raw[['SubjectID', 'feature_delta', 'Q3_Swallowing']].reindex(columns=['SubjectID', 'Q3_Swallowing', 'feature_delta'])
alsfrs_Sw = alsfrs_Sw[alsfrs_Sw['feature_delta']>=0]
alsfrs_Sw

alsfrs_Sw_grouped = alsfrs_Sw.groupby('SubjectID').agg(['first', 'last'])
alsfrs_Sw_grouped = alsfrs_Sw_grouped.reset_index()
alsfrs_Sw_grouped = alsfrs_Sw_grouped[alsfrs_Sw_grouped[('feature_delta', 'last')]!= alsfrs_Sw_grouped[('feature_delta', 'first')]] # more than 2 observation needed (score chagnes from above 2 to 2)
alsfrs_filtered_extent = list(alsfrs_Sw_grouped[alsfrs_Sw_grouped[('Q3_Swallowing','first')]>2].reset_index()['SubjectID']) # initial ALSFRS Q3 > 2

# Subtract [FVC < 50] & [first ALSFRS Q3 <=2.0] & [ALSFRS Q3 observed only once]
alsfrs_Sw_filtered = alsfrs_Sw.query("SubjectID == {0}".format(fvc_filtered_extent))
alsfrs_Sw_filtered = alsfrs_Sw_filtered.query("SubjectID == {0}".format(alsfrs_filtered_extent))

"""### (3) Time of [Q3 score == 2.0]"""

# Find the first time of [ALSFRS_Q3 <= 2.0]
Optimal_event = alsfrs_Sw_filtered[alsfrs_Sw_filtered['Q3_Swallowing']<=2].groupby('SubjectID').agg(['first']).reset_index()

# Coding [ALSFRS-Q3<=2] event as '1'
Optimal_event_1 = Optimal_event[[(    'SubjectID',      ''), ('feature_delta', 'first')]]
Optimal_event_1.columns = ['SubjectID', 'time_opt']

Optimal_event_1_sublist = list(Optimal_event['SubjectID'])

Optimal_event_1['status_opt'] = 1
print("There are",len(Optimal_event_1['SubjectID'].unique()), "subjects whose status_opt = 1")

# Otherwise '0'
Optimal_event_0 = alsfrs_Sw_filtered[~alsfrs_Sw_filtered['SubjectID'].isin(Optimal_event_1_sublist)]
Optimal_event_0 = Optimal_event_0.groupby('SubjectID').agg(['last']).reset_index().drop(columns=('Q3_Swallowing', 'last'))
Optimal_event_0.columns = ['SubjectID', 'time_opt']
Optimal_event_0['status_opt'] = 0
print("There are",len(Optimal_event_0['SubjectID'].unique()), "subjects whose status_opt = 0")
 # There are 1515 subjects whose status_opt = 1
 # There are 3008 subjects whose status_opt = 0

alsfrs_Sw_coded = pd.concat([Optimal_event_1, Optimal_event_0]).sort_values(by='SubjectID', axis=0)
alsfrs_Sw_coded = alsfrs_Sw_coded.reset_index()
alsfrs_Sw_coded.drop(columns='index', inplace=True)

Optimal_Gas = alsfrs_Sw_coded.copy()
sub_list = list(Optimal_Gas['SubjectID'])
Optimal_Gas #4523 data

Optimal_Gas.to_csv('/content/drive/MyDrive/Colab Notebooks/본 실험/PACTALS/dataset/0815/0817_optimal_target.csv')

"""## 2-2. Real target

### (1) Time of [ALSFRS Q5_b != NaN]
"""

gastro = alsfrs_q_raw[['SubjectID', 'Q5b_Cutting_with_Gastrostomy', 'feature_delta']].sort_values(by=['SubjectID', 'feature_delta'], axis=0).reset_index().drop(columns='index')
gastro

# Check censored data
def checking_censored(x):
  
  if x.isnull().sum() == 0:
    return "Left censored"
  elif x.notnull().sum() == 0:
    return "Right censored"
  else:
    return "Normal"

aggs_by_col = {'Q5b_Cutting_with_Gastrostomy': [checking_censored], 'feature_delta': ['last']}
gastro_a = gastro.groupby('SubjectID', as_index=False).agg(aggs_by_col)
gastro_a

#Subtract Left censored data

gastro_a.columns = ['SubjectID', 'checking_censored', 'last_feature_delta']
gastro_a = gastro_a[gastro_a['checking_censored'] != 'Left censored']
full_extent = list(gastro_a['SubjectID'])
Right_censored_extent = list(gastro_a[gastro_a['checking_censored'] == 'Right censored']['SubjectID'])
Normal_extent = list(gastro_a[gastro_a['checking_censored'] == 'Normal']['SubjectID'])

print("Total number is " + str(len(full_extent))) # Total number is 5797
print("There are " + str(len(Right_censored_extent)) + " right censored data") # There are 4609 right censored data
print("There are " + str(len(Normal_extent)) + " normal data") # There are 1188 normal data

# Create gastro_event_0
gastro_event_0 = gastro_a[gastro_a['checking_censored'] == 'Right censored']
gastro_event_0 = gastro_event_0.replace({'checking_censored':{'Right censored': 0}})
gastro_event_0.columns = ['SubjectID', 'status', 'time']
gastro_event_0 #4609 data

# Create gastro_event_1
gastro_b = gastro.copy()
gastro_b.query("SubjectID == {0}".format(Normal_extent), inplace=True)
gastro_b = gastro_b.dropna(axis=0)
gastro_event_1 = pd.DataFrame(gastro_b.groupby('SubjectID')['feature_delta'].agg('first')).reset_index()
gastro_event_1.columns = ['SubjectID', 'time']
gastro_event_1['status'] = 1
gastro_event_1 = gastro_event_1[gastro_event_1['time'] != 0] # time != 0 
gastro_event_1 #970 data

gastro_fin = pd.concat([gastro_event_1, gastro_event_0]).sort_values(by='SubjectID', axis=0)
gastro_fin = gastro_fin.reset_index().drop(columns = 'index')
gastro_fin.columns = ['SubjectID', 'time_real', 'status_real']
gastro_fin = gastro_fin[gastro_fin['time_real']>92]
Real_Gas = gastro_fin.copy()
Real_Gas # 5027 data

Real_Gas.to_csv('/content/drive/MyDrive/Colab Notebooks/본 실험/PACTALS/dataset/0815/0817_optimal_target.csv')

"""## 2-3. Comparing proportion of censored data in Optimal gas/ Real gas / Survival"""

# Read datasets needed
from google.colab import files 
uploaded = files.upload()

# import raw data 원준용
import io
surv = pd.read_csv(io.BytesIO(uploaded['survival.csv']))

event_distribution = pd.DataFrame(Optimal_Gas[['status_opt']].value_counts()).reset_index()
event_distribution.columns = ['status_o', 'count']
event_distribution['status_o'] = event_distribution['status_o'].astype('bool')
event_distribution = event_distribution.replace({'status_o': {False:'0 (censored)', True:'1 (occured)'}})
print(event_distribution)

event_distribution_2 = pd.DataFrame(surv[['status']].value_counts()).reset_index()
event_distribution_2.columns = ['status_surv', 'count']
event_distribution_2['status_surv'] = event_distribution_2['status_surv'].astype('bool')
event_distribution_2 = event_distribution_2.replace({'status_surv': {False:'0 (censored)', True:'1 (occured)'}})
print(event_distribution_2)

event_distribution_3 = pd.DataFrame(Real_Gas[['status_real']].value_counts()).reset_index()
event_distribution_3.columns = ['status_real', 'count']
event_distribution_3['status_real'] = event_distribution_3['status_real'].astype('bool')
event_distribution_3 = event_distribution_3.replace({'status_real': {False:'0 (censored)', True:'1 (occured)'}})
print(event_distribution_3)

A_1 = event_distribution.iloc[0]['count']
B_1 = event_distribution.iloc[1]['count']
per_0 = str(round((A_1/(A_1+B_1))*100,2))+"%"
per_1 = str(round((B_1/(A_1+B_1))*100,2))+'%'

A = event_distribution_2.iloc[0]['count']
B = event_distribution_2.iloc[1]['count']
perc_0 = str(round((A/(A+B))*100,2))+"%"
perc_1 = str(round((B/(A+B))*100,2))+'%'

A_2 = event_distribution_3.iloc[0]['count']
B_2 = event_distribution_3.iloc[1]['count']
pe_0 = str(round((A_2/(A_2+B_2))*100,2))+"%"
pe_1 = str(round((B_2/(A_2+B_2))*100,2))+'%'


#        status_o  count
# 0  0 (censored)   3008
# 1   1 (occured)   1515
#     status_surv  count
# 0  0 (censored)   6005
# 1   1 (occured)   3075
#     status_real  count
# 0  0 (censored)   4220
# 1   1 (occured)    807

plt.figure(figsize=(15, 6))

plt.subplot(131)
plt.bar(event_distribution['status_o'], height=event_distribution['count'], color=['green', 'orange'])
plt.ylim([0,7000])
plt.title('Event Distribution (Optimal Gastrostomy)')
plt.text(-0.12,1600,per_0)
plt.text(0.85,700,per_1)

plt.subplot(132)
plt.bar(event_distribution_2['status_surv'], height=event_distribution_2['count'], color=['green', 'orange'])
plt.ylim([0,7000])
plt.title('Event Distribution (Survival)')
plt.text(-0.15,1500,perc_0)
plt.text(0.85,550,perc_1)

plt.subplot(133)
plt.bar(event_distribution_3['status_real'], height=event_distribution_3['count'], color=['green', 'orange'])
plt.ylim([0,7000])
plt.title('Event Distribution (Real Gastrostomy)')
plt.text(-0.15,1500,pe_0)
plt.text(0.85,300,pe_1)

plt.show()