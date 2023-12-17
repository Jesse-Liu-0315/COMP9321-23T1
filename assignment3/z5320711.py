import pandas as pd
import numpy as np 
import seaborn as sns 
import sklearn
from sklearn.feature_extraction import text 
from sklearn.feature_extraction.text import CountVectorizer 
from sklearn.metrics import confusion_matrix, mean_squared_error, r2_score 
from sklearn.model_selection import train_test_split 
from sklearn.feature_selection import SelectKBest 
import matplotlib.pyplot as plt 
from sklearn.metrics import confusion_matrix 
from sklearn.neighbors import KNeighborsClassifier 
from sklearn.utils import shuffle
from sklearn.metrics import precision_score, accuracy_score, recall_score 
from sklearn.model_selection import train_test_split
from sklearn.feature_selection import RFE
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import LabelEncoder
import statsmodels.api as sm
from scipy.stats import pearsonr
from sklearn.ensemble import RandomForestRegressor
from sklearn.discriminant_analysis import StandardScaler
from sklearn.preprocessing import PolynomialFeatures
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_recall_fscore_support

################################################Question 1################################################
# Read TSV file
train = pd.read_csv('train.tsv', sep='\t')
test = pd.read_csv('test.tsv', sep='\t')
# Drop rows with missing values
train.dropna(inplace=True)
# Handling abnormal values
train = train[(train['revenue'] > 0) & (train['revenue'] < 1e6)]
# remove the stop word in ATM_Location_TYPE
stop_words = text.ENGLISH_STOP_WORDS.union(['Only', 'and'])
train['ATM_Location_TYPE'] = train['ATM_Location_TYPE'].apply(lambda x: ' '.join([word for word in x.split() if word not in (stop_words)]))
test['ATM_Location_TYPE'] = test['ATM_Location_TYPE'].apply(lambda x: ' '.join([word for word in x.split() if word not in (stop_words)]))
# add feature
train['perhouse'] = train['Estimated_Number_of_Houses_in_1_KM_Radius'] / train['No_of_Other_ATMs_in_1_KM_radius']
test['perhouse'] = test['Estimated_Number_of_Houses_in_1_KM_Radius'] / test['No_of_Other_ATMs_in_1_KM_radius']

train['ATM_Location_TYPE'] = train['ATM_Location_TYPE'].str.split(' ')
train = train.explode('ATM_Location_TYPE')
# Encode the string values to numeric values
# columns = ['ATM_Zone', 'ATM_Placement', 'ATM_TYPE', 'ATM_Location_TYPE', 'ATM_looks', 'ATM_Attached_to', 'Day_Type'] need to be encoded
cols_to_transform = [ 'ATM_Zone', 'ATM_Placement', 'ATM_TYPE', 'ATM_Location_TYPE', 'ATM_looks', 'ATM_Attached_to', 'Day_Type']

# define the LabelEncoder
le = LabelEncoder()
# apply the LabelEncoder to the columns
for col in cols_to_transform:
    le.fit(train[col].unique().tolist() + test[col].unique().tolist())
    
    # Convert each column in the dataset to an integer.
    train[col] = le.transform(train[col])
    test[col] = le.transform(test[col])

# Standardizing/normalizing data
#scaler = StandardScaler()
#train[['Estimated_Number_of_Houses_in_1_KM_Radius']] = scaler.fit_transform(train[['Estimated_Number_of_Houses_in_1_KM_Radius']])
#test[['Estimated_Number_of_Houses_in_1_KM_Radius']] = scaler.fit_transform(test[['Estimated_Number_of_Houses_in_1_KM_Radius']])

# PolynomialFeatures
#poly = PolynomialFeatures(degree=2, include_bias=False)
#train_poly = poly.fit_transform(train.drop(['revenue'], axis=1))
#train_poly = pd.DataFrame(train_poly, columns=poly.get_feature_names(train.columns[:-1]))


# Divide the data into independent variables and dependent variables.
X = train.drop(['revenue'], axis=1)
Y = train['revenue']

# Backward Elimination Feature Selection
while True:
    # Fitting model
    model = sm.OLS(Y, sm.add_constant(X)).fit()
    # Calculate the p-value for each feature.
    p_values = model.pvalues.iloc[1:]
    #print(p_values)
    # Select the feature with the highest p-value.
    max_p_value = p_values.max()
    # If the maximum p-value is greater than 0.05, then delete that feature.
    if max_p_value > 0.05:
        feature_to_drop = p_values.idxmax()
        X = X.drop([feature_to_drop], axis=1)
        test = test.drop([feature_to_drop], axis=1)
    # If the maximum p-value is less than or equal to 0.05, stop iterating.
    else:
        break


model = RandomForestRegressor(n_estimators=180, max_depth=30, random_state=42)
model.fit(X, Y)
y_pred = model.predict(test.drop(['revenue'], axis=1))

# calculate Pearson correlation coefficientt for the model

corr, p_value = pearsonr(test['revenue'], y_pred)
y_pred = pd.DataFrame(y_pred, columns=['predicted_revenue'])
y_pred.to_csv('z5320711.PART1.output.csv', index=False)

################################################Question 2################################################
# Read TSV file
train = pd.read_csv('train.tsv', sep='\t')
test = pd.read_csv('test.tsv', sep='\t')
# Drop rows with missing values
train.dropna(inplace=True)
# Handling abnormal values
train = train[(train['revenue'] > 0) & (train['revenue'] < 1e6)]
train = train[(train['rating'] != 0)] # rating is between 1 and 5
# remove the stop word in ATM_Location_TYPE
stop_words = text.ENGLISH_STOP_WORDS.union(['Only', 'and'])
train['ATM_Location_TYPE'] = train['ATM_Location_TYPE'].apply(lambda x: ' '.join([word for word in x.split() if word not in (stop_words)]))
test['ATM_Location_TYPE'] = test['ATM_Location_TYPE'].apply(lambda x: ' '.join([word for word in x.split() if word not in (stop_words)]))
# add feature
train['perhouse'] = train['Estimated_Number_of_Houses_in_1_KM_Radius'] / train['No_of_Other_ATMs_in_1_KM_radius']
test['perhouse'] = test['Estimated_Number_of_Houses_in_1_KM_Radius'] / test['No_of_Other_ATMs_in_1_KM_radius']
train['ATM_Location_TYPE'] = train['ATM_Location_TYPE'].str.split(' ')
train = train.explode('ATM_Location_TYPE')
# Encode the string values to numeric values
# columns = ['ATM_Zone', 'ATM_Placement', 'ATM_TYPE', 'ATM_Location_TYPE', 'ATM_looks', 'ATM_Attached_to', 'Day_Type'] need to be encoded
cols_to_transform = [ 'ATM_Zone', 'ATM_Placement', 'ATM_TYPE', 'ATM_Location_TYPE', 'ATM_looks', 'ATM_Attached_to', 'Day_Type']

# define the LabelEncoder
le = LabelEncoder()
# apply the LabelEncoder to the columns
for col in cols_to_transform:
    le.fit(train[col].unique().tolist() + test[col].unique().tolist())
    
    # Convert each column in the dataset to an integer.
    train[col] = le.transform(train[col])
    test[col] = le.transform(test[col])

# Standardizing/normalizing data
#scaler = StandardScaler()
#train[['Estimated_Number_of_Houses_in_1_KM_Radius']] = scaler.fit_transform(train[['Estimated_Number_of_Houses_in_1_KM_Radius']])
#test[['Estimated_Number_of_Houses_in_1_KM_Radius']] = scaler.fit_transform(test[['Estimated_Number_of_Houses_in_1_KM_Radius']])

# PolynomialFeatures
#poly = PolynomialFeatures(degree=2, include_bias=False)
#train_poly = poly.fit_transform(train.drop(['revenue'], axis=1))
#train_poly = pd.DataFrame(train_poly, columns=poly.get_feature_names(train.columns[:-1]))

# add new feature
train['ATM_Zone'] = train['ATM_Zone'] * train['ATM_Placement']
test['ATM_Zone'] = test['ATM_Zone'] * test['ATM_Placement']
#train['ATM_ty'] = train['ATM_TYPE'] * train['ATM_Location_TYPE']
#test['ATM_ty'] = test['ATM_TYPE'] * test['ATM_Location_TYPE']
train['ATM_looks_attach'] = train['ATM_looks'] * train['ATM_Attached_to']
test['ATM_looks_attach'] = test['ATM_looks'] * test['ATM_Attached_to']
train['ATM_looks_type'] = train['ATM_looks'] * train['ATM_TYPE']
test['ATM_looks_type'] = test['ATM_looks'] * test['ATM_TYPE']

# Divide the data into independent variables and dependent variables.
X = train.drop(['rating'], axis=1)
Y = train['rating']

# Backward Elimination Feature Selection
while True:
    # Fitting model
    model = sm.OLS(Y, sm.add_constant(X)).fit()
    # Calculate the p-value for each feature.
    p_values = model.pvalues.iloc[1:]
    #print(p_values)
    # Select the feature with the highest p-value.
    max_p_value = p_values.max()
    # If the maximum p-value is greater than 0.05, then delete that feature.
    if max_p_value > 0.05:
        feature_to_drop = p_values.idxmax()
        X = X.drop([feature_to_drop], axis=1)
        test = test.drop([feature_to_drop], axis=1)
    # If the maximum p-value is less than or equal to 0.05, stop iterating.
    else:
        break


clf = RandomForestClassifier(n_estimators=200, random_state=42)
clf.fit(X, Y)


y_pred = clf.predict(test.drop(['rating'], axis=1))
y_pred = pd.DataFrame(y_pred, columns=['predicted_rating'])
y_pred.to_csv('z5320711.PART2.output.csv', index=False)
