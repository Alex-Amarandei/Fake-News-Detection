# -*- coding: utf-8 -*-
"""Fake News Detection.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1n67Sr7KUGPg-HhDcx36lWeVll0Pq54an

# Imports
"""

import re
import nltk
import spacy
import string
import pickle
import itertools
import numpy as np
import pandas as pd
import seaborn as sns
from empath import Empath
from nltk import tokenize
import scipy.sparse as sp
from sklearn import metrics
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.naive_bayes import ComplementNB
from sklearn.metrics import confusion_matrix
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import classification_report
from sklearn.neighbors import KNeighborsClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import PassiveAggressiveClassifier
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier

"""# Downloads"""

!pip install empath
nltk.download('words')
nltk.download('wordnet')
nltk.download('stopwords')

"""# Configurations"""

# To see more of the output
pd.set_option('display.max_colwidth', 1000)

"""# Utility Functions

## Cleaning Function
"""

def clean_text(text):
  text = re.sub('['+string.punctuation+']','', text)
  text = re.sub(r"[-()\"#/@’;:<>{}`+=~|.!?,]", '', text)
  text = text.lower().split()

  stops = set(stopwords.words("english"))
  text = [w for w in text if w not in stops]
  text = " ".join(text)
  
  text = re.sub(r'[^a-zA-Z\s]', u'', text, flags=re.UNICODE)
  
  text = text.split()
  l = WordNetLemmatizer()
  lemmatized_words = [l.lemmatize(word) for word in text if len(word) > 2]
  text = " ".join(lemmatized_words)
    
  return text

"""## Confusion Matrix Configuration"""

def plot_confusion_matrix(cm, classes, normalize=False, title='Confusion matrix', cmap=plt.cm.Blues):
    plt.imshow(cm, interpolation='nearest', cmap=cmap)
    plt.title(title)
    plt.colorbar()
    tick_marks = np.arange(len(classes))
    plt.xticks(tick_marks, classes, rotation=0)
    plt.yticks(tick_marks, classes)

    thresh = cm.max() / 2.
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        plt.text(j, i, cm[i, j],
                 horizontalalignment="center",
                 color="white" if cm[i, j] > thresh else "black")

    plt.tight_layout()
    plt.ylabel('Actual label')
    plt.xlabel('Predicted label')
    plt.tight_layout()
    plt.show()

"""# Dataset Importing

## Importing raw data
"""

data = pd.read_csv("data.tsv", delimiter='\t', encoding='mac_roman')

print(data.shape)
print(data.columns)
data.head()

data2 = pd.read_csv("data2.tsv", delimiter='\t', encoding='mac_roman')

indexNames = data2[data2['our rating'] == 'false'].index
data2.drop(indexNames , inplace=True)

print(data2.shape)
print(data2.columns)
data2.head()

data = data.append(data2, ignore_index = True)

print(data.shape)
data.head()

"""## Data Manipulation

### Label Capitalizing
"""

data.loc[data['our rating'] == 'true', 'our rating'] = 'TRUE'
data.loc[data['our rating'] == 'false', 'our rating'] = 'FALSE'
data.loc[data['our rating'] == 'partially false', 'our rating'] = 'PARTIALLY FALSE'
data.loc[data['our rating'] == 'other', 'our rating'] = 'OTHER'

data.head()

"""### Combining the **title** and **text** columns"""

data['text'] = data['title'] + " " + data['text']

data.head()

"""### Extra columns removal"""

data.drop(columns=['title'], inplace = True)

data.head()

"""### Label Distribution"""

data['our rating'].value_counts()
data['our rating'].value_counts().plot(kind = 'bar')

"""# First Approach - Simple TFIDF Analysis

## Data Preparation

### Creating an Additional Column with Cleaned Text
"""

data['clean_text'] = data['text'].astype('str').apply(lambda x: clean_text(x))

data.head()

"""## Data Exploration

### Word Cloud View: FALSE Label
"""

fake_data = data[data["our rating"] == "FALSE"].astype('str')
all_words = ' '.join([text for text in fake_data.text])

word_cloud = WordCloud(width = 1000, height = 1000, max_font_size = 110, collocations = False).generate(all_words)

plt.figure(figsize = (10, 7))
plt.imshow(word_cloud, interpolation = 'bilinear')
plt.axis("off")

"""### Word Cloud View: TRUE Label"""

true_data = data[data["our rating"] == "TRUE"].astype('str')
all_words = ' '.join([text for text in true_data.text])

word_cloud = WordCloud(width = 1000, height = 1000, max_font_size = 110, collocations = False).generate(all_words)
plt.figure(figsize = (10, 7))
plt.imshow(word_cloud, interpolation = 'bilinear')
plt.axis("off")

"""### Word Cloud View: PARTIALLY FALSE Label"""

partially_false_data = data[data["our rating"] == "PARTIALLY FALSE"].astype('str')
all_words = ' '.join([text for text in partially_false_data.text])

word_cloud = WordCloud(width = 1000, height = 1000, max_font_size = 110, collocations = False).generate(all_words)
plt.figure(figsize = (10, 7))
plt.imshow(word_cloud, interpolation = 'bilinear')
plt.axis("off")

"""### Word Cloud View: OTHER Label"""

other_data = data[data["our rating"] == "OTHER"].astype('str')
all_words = ' '.join([text for text in other_data.text])

word_cloud = WordCloud(width = 1000, height = 1000, max_font_size = 110, collocations = False).generate(all_words)
plt.figure(figsize = (10, 7))
plt.imshow(word_cloud, interpolation = 'bilinear')
plt.axis("off")

"""## Train and Test Split"""

y = data['our rating'].astype('str') 
X_train, X_test, y_train, y_test = train_test_split(data['clean_text'], y, test_size = 0.2, random_state = 42)

print(X_train.head())
print()
print(y_train.head())

"""## TFIDF Vectorization"""

tfidf_vectorizer = TfidfVectorizer(stop_words = 'english', ngram_range = (2, 2))

tfidf_train = tfidf_vectorizer.fit_transform(X_train)

tfidf_test = tfidf_vectorizer.transform(X_test)

print(tfidf_vectorizer.get_feature_names()[:100])

"""## Model Testing

### Naive-Bayes Alpha-Tuning
"""

alphas = np.arange(0, 1, 0.1)

def train_and_predict(alpha, x_train, x_test):
    nb_classifier = MultinomialNB(alpha=alpha)
    nb_classifier.fit(x_train, y_train)
    pred = nb_classifier.predict(x_test)
    score = metrics.accuracy_score(y_test, pred)
    return score

for alpha in alphas:
  print('Alpha: ', alpha)
  print('Score: ', train_and_predict(alpha, tfidf_train, tfidf_test))
  print()

"""### Naive-Bayes (with best parameters)"""

nb_classifier = MultinomialNB(alpha=0.0)
nb_classifier.fit(tfidf_train, y_train)

pred = nb_classifier.predict(tfidf_test)
print(classification_report(y_test, pred))

cm = metrics.confusion_matrix(y_test, pred, labels=['FALSE', 'TRUE', 'PARTIALLY FALSE', 'OTHER'])
print('Confusion Matrix: ')
print(cm)
plot_confusion_matrix(cm, classes=['FALSE', 'TRUE', 'PARTIALLY', 'OTHER'])

"""### K Nearest Neighbors Hyper-Parameter Tuning"""

knn_params = RandomizedSearchCV(estimator=KNeighborsClassifier(), param_distributions={
    "leaf_size": list(range(1, 50)),
    "n_neighbors": list(range(1, 30)),
    "p": [1, 2]
}, n_iter=100, n_jobs=-1)

result = knn_params.fit(tfidf_train, y_train)
result_df = pd.DataFrame(result.cv_results_).loc[[result.best_index_]]

print(result_df["params"])

"""### K Nearest Neighbors (with best parameters)"""

knn_classifier = KNeighborsClassifier(p=2, n_neighbors=29, leaf_size=17)
knn_classifier.fit(tfidf_train, y_train)

pred = knn_classifier.predict(tfidf_test)
print(classification_report(y_test, pred))

cm = metrics.confusion_matrix(y_test, pred, labels=['FALSE', 'TRUE', 'PARTIALLY FALSE', 'OTHER'])
print('Confusion Matrix: ')
print(cm)
plot_confusion_matrix(cm, classes=['FALSE', 'TRUE', 'PARTIALLY', 'OTHER'])

"""### Random Forest Hyper-Parameter Tuning"""

rf_params = RandomizedSearchCV(estimator=RandomForestClassifier(), param_distributions={
    "n_estimators" : [200, 400, 600, 800, 1000],
    "max_features" : ['auto', 'sqrt'],
    "max_depth" : [10, 20, 30, 40, 50, None],
    "min_samples_split" : [2, 5, 10],
    "min_samples_leaf" : [1, 2, 4]
}, n_iter=10, n_jobs=-1)

result = rf_params.fit(tfidf_train, y_train)
result_df = pd.DataFrame(result.cv_results_).loc[[result.best_index_]]

print(result_df["params"])

"""
### Random Forest (with best parameters)"""

rf_classifier = RandomForestClassifier(verbose=True, n_estimators = 1000, max_features = 'sqrt', max_depth = 50, min_samples_split = 2, min_samples_leaf = 2)
rf_classifier.fit(tfidf_train, y_train)

pred = rf_classifier.predict(tfidf_test)
print(classification_report(y_test, pred))

cm = metrics.confusion_matrix(y_test, pred, labels=['FALSE', 'TRUE', 'PARTIALLY FALSE', 'OTHER'])
print('Confusion Matrix: ')
print(cm)
plot_confusion_matrix(cm, classes=['FALSE', 'TRUE', 'PARTIALLY', 'OTHER'])

"""### Gradient Boosting (with default parameters)"""

gb_classifier = GradientBoostingClassifier(verbose=True, n_estimators = 200)
gb_classifier.fit(tfidf_train, y_train)

pred = gb_classifier.predict(tfidf_test)
print(classification_report(y_test, pred))

cm = metrics.confusion_matrix(y_test, pred, labels=['FALSE', 'TRUE', 'PARTIALLY FALSE', 'OTHER'])
print('Confusion Matrix: ')
print(cm)
plot_confusion_matrix(cm, classes=['FALSE', 'TRUE', 'PARTIALLY', 'OTHER'])

"""# Second Approach - POS Tagging

## Data Preparation
"""

nlp = spacy.load('en')
pos_tags_column = []

for text in data['text'].astype('str'):
    pos_tags = []
    doc = nlp(text)
    for token in doc:
        pos_tags.append(token.pos_)
    all_pos_tags = ' '.join(pos_tags)
    pos_tags_column.append(all_pos_tags)
    
data['POS_text'] = pos_tags_column

data.head()

"""## Data Exploration

### Counter Function
"""

token_space = tokenize.WhitespaceTokenizer()

def counter(text, column_text, quantity):
    words = ' '.join([text for text in text[column_text]])
    token_phrase = token_space.tokenize(words)
    frequency = nltk.FreqDist(token_phrase)
    df_frequency = pd.DataFrame({"Word": list(frequency.keys()), "Frequency": list(frequency.values())})
    df_frequency = df_frequency.nlargest(columns="Frequency", n=quantity)
    plt.figure(figsize=(12, 8))
    ax = sns.barplot(data=df_frequency, x="Word", y="Frequency", color='blue')
    ax.set(ylabel="Count")
    plt.xticks(rotation='vertical')
    plt.show()

"""### Most Frequent POS in FALSE Labeled texts"""

counter(data[data["our rating"] == "FALSE"], "POS_text", 20)

"""### Most Frequent POS in TRUE Labeled texts"""

counter(data[data["our rating"] == "TRUE"], "POS_text", 20)

"""### Most Frequent POS in PARTIALLY FALSE Labeled texts"""

counter(data[data["our rating"] == "PARTIALLY FALSE"], "POS_text", 20)

"""### Most Frequent POS in OTHER Labeled texts"""

counter(data[data["our rating"] == "OTHER"], "POS_text", 20)

"""## Train and Test Split"""

y = data['our rating'].astype('str')
X_train, X_test, y_train, y_test = train_test_split(data['POS_text'], y, test_size = 0.2, random_state = 42)

print(X_train.head())
print(y_train.head())

"""## TFIDF Vectorization"""

pos_tfidf_vectorizer = TfidfVectorizer(stop_words='english', ngram_range = (2,2))
pos_tfidf_train = pos_tfidf_vectorizer.fit_transform(X_train.astype('str'))
pos_tfidf_test= pos_tfidf_vectorizer.transform(X_test.astype('str'))
pos_tfidf_vectorizer.get_feature_names()[:10]

"""## Model Testing

### Naive-Bayes Alpha-Tuning
"""

for alpha in alphas:
  print('Alpha: ', alpha)
  print('Score: ', train_and_predict(alpha, pos_tfidf_train, pos_tfidf_test))
  print()

"""### Naive-Bayes (with best parameters)"""

nb_classifier = MultinomialNB(alpha = 0.0)
nb_classifier.fit(pos_tfidf_train, y_train)

pred = nb_classifier.predict(pos_tfidf_test)
print(classification_report(y_test, pred))

cm = metrics.confusion_matrix(y_test, pred, labels=['FALSE', 'TRUE', 'PARTIALLY FALSE', 'OTHER'])
print('Confusion Matrix: ')
print(cm)
plot_confusion_matrix(cm, classes=['FALSE', 'TRUE', 'PARTIALLY', 'OTHER'])

"""### K Nearest Neighbors Hyper-Parameter Tuning"""

knn_params = RandomizedSearchCV(estimator=KNeighborsClassifier(), param_distributions={
    "leaf_size": list(range(1, 50)),
    "n_neighbors": list(range(1, 30)),
    "p": [1, 2]
}, n_iter=100, n_jobs=-1)

result = knn_params.fit(pos_tfidf_train, y_train)
result_df = pd.DataFrame(result.cv_results_).loc[[result.best_index_]]

print(result_df["params"])

"""### K Nearest Neighbors (with best parameters)"""

knn_classifier = KNeighborsClassifier(p = 1, n_neighbors = 25, leaf_size = 35)
knn_classifier.fit(pos_tfidf_train, y_train)

pred = knn_classifier.predict(pos_tfidf_test)
print(classification_report(y_test, pred))

cm = metrics.confusion_matrix(y_test, pred, labels=['FALSE', 'TRUE', 'PARTIALLY FALSE', 'OTHER'])
plot_confusion_matrix(cm, classes=['FALSE', 'TRUE', 'PARTIALLY', 'OTHER'])

"""### Random Forest Hyper-Parameter Tuning"""

rf_params = RandomizedSearchCV(estimator=RandomForestClassifier(), param_distributions={
    "n_estimators" : [200, 400, 600, 800, 1000],
    "max_features" : ['auto', 'sqrt'],
    "max_depth" : [10, 20, 30, 40, 50, None],
    "min_samples_split" : [2, 5, 10],
    "min_samples_leaf" : [1, 2, 4]
}, n_iter=10, n_jobs=-1)

result = rf_params.fit(pos_tfidf_train, y_train)
result_df = pd.DataFrame(result.cv_results_).loc[[result.best_index_]]

print(result_df["params"])

"""### Random Forest (with best parameters)"""

rf_classifier = RandomForestClassifier(n_estimators = 400, min_samples_split = 10, min_samples_leaf = 4, max_features = 'sqrt', max_depth = 30)
rf_classifier.fit(pos_tfidf_train, y_train)

pred = rf_classifier.predict(pos_tfidf_test)
print(classification_report(y_test, pred))

cm = metrics.confusion_matrix(y_test, pred, labels=['FALSE', 'TRUE', 'PARTIALLY FALSE', 'OTHER'])
print('Confusion Matrix: ')
print(cm)
plot_confusion_matrix(cm, classes=['FALSE', 'TRUE', 'PARTIALLY', 'OTHER'])

"""### Gradient Boosting (with default parameters)"""

gb_classifier = GradientBoostingClassifier(verbose=True, n_estimators = 200)
gb_classifier.fit(pos_tfidf_train, y_train)

pred = gb_classifier.predict(pos_tfidf_test)
print(classification_report(y_test, pred))

cm = metrics.confusion_matrix(y_test, pred, labels=['FALSE', 'TRUE', 'PARTIALLY FALSE', 'OTHER'])
print('Confusion Matrix: ')
print(cm)
plot_confusion_matrix(cm, classes=['FALSE', 'TRUE', 'PARTIALLY', 'OTHER'])

"""# Third Approach - Semantic Analysis

## Data Preparation
"""

lexicon = Empath()
semantic = []
count = 0

for article in data['text'].astype('str'):
    print(article)
    d = lexicon.analyze(article, normalize=False)
    print(d)
    x = []
    for key, value in d.items():
        x.append(value)
    x = np.asarray(x)
    semantic.append(x)
data['semantic_text'] = semantic

print(data['semantic_text'].head())

categories = []
a = lexicon.analyze("")
for key, value in a.items():
    categories.append(key)
    
categories

sem = []
for i in range(data.shape[0]):
    a = []
    for j in range(len(semantic[0])):
        for k in range(int(semantic[i][j])):
            a.append(categories[j])
    b = " ".join(a)
    sem.append(b)
data['semantics_text'] = sem

print(data['semantics_text'].head())

"""## Data Exploration

### Most Frequent Subjects in FALSE Labeled texts
"""

counter(data[data["our rating"] == "FALSE"], "semantics_text", 20)

"""### Most Frequent Subjects in TRUE Labeled texts"""

counter(data[data["our rating"] == "TRUE"], "semantics_text", 20)

"""### Most Frequent Subjects in PARTIALLY FALSE Labeled texts"""

counter(data[data["our rating"] == "PARTIALLY FALSE"], "semantics_text", 20)

"""### Most Frequent Subjects in OTHER Labeled texts"""

counter(data[data["our rating"] == "OTHER"], "semantics_text", 20)

"""## Train and Test Split"""

y = data['our rating'].astype('str')
X_train, X_test, y_train, y_test = train_test_split(data['semantics_text'], y, test_size = 0.2, random_state = 42)

print(X_train.head())
print(y_train.head())

"""## TFIDF Vectorizer"""

sem_tfidf_vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1,1))
sem_tfidf_train = sem_tfidf_vectorizer.fit_transform(X_train.astype('str'))
sem_tfidf_test = sem_tfidf_vectorizer.transform(X_test.astype('str'))

"""## Model Testing

### Naive-Bayes Alpha-Tuning
"""

for alpha in alphas:
  print('Alpha: ', alpha)
  print('Score: ', train_and_predict(alpha, sem_tfidf_train, sem_tfidf_test))
  print()

"""### Naive-Bayes (with best parameters)"""

nb_classifier = MultinomialNB(alpha=0.1)
nb_classifier.fit(sem_tfidf_train, y_train)

pred = nb_classifier.predict(sem_tfidf_test)
print(classification_report(y_test, pred))

cm = metrics.confusion_matrix(y_test, pred, labels=['FALSE', 'TRUE', 'PARTIALLY FALSE', 'OTHER'])
print('Confusion Matrix: ')
print(cm)
plot_confusion_matrix(cm, classes=['FALSE', 'TRUE', 'PARTIALLY', 'OTHER'])

"""### K Nearest Neighbors Hyper-Parameter Tuning"""

knn_params = RandomizedSearchCV(estimator=KNeighborsClassifier(), param_distributions={
    "leaf_size": list(range(1, 50)),
    "n_neighbors": list(range(1, 30)),
    "p": [1, 2]
}, n_iter=100, n_jobs=-1)

result = knn_params.fit(sem_tfidf_train, y_train)
result_df = pd.DataFrame(result.cv_results_).loc[[result.best_index_]]

print(result_df["params"])

"""### K Nearest Neighbors (with best parameters)"""

knn_classifier = KNeighborsClassifier(p = 2, n_neighbors = 27, leaf_size = 12)
knn_classifier.fit(sem_tfidf_train, y_train)

pred = knn_classifier.predict(sem_tfidf_test)
print(classification_report(y_test, pred))

cm = metrics.confusion_matrix(y_test, pred, labels=['FALSE', 'TRUE', 'PARTIALLY FALSE', 'OTHER'])
plot_confusion_matrix(cm, classes=['FALSE', 'TRUE', 'PARTIALLY', 'OTHER'])

"""### Random Forest Hyper-Parameter Tuning"""

rf_params = RandomizedSearchCV(estimator=RandomForestClassifier(), param_distributions={
    "n_estimators" : [200, 400, 600, 800, 1000],
    "max_features" : ['auto', 'sqrt'],
    "max_depth" : [10, 20, 30, 40, 50, None],
    "min_samples_split" : [2, 5, 10],
    "min_samples_leaf" : [1, 2, 4]
}, n_iter=10, n_jobs=-1)

result = rf_params.fit(sem_tfidf_train, y_train)
result_df = pd.DataFrame(result.cv_results_).loc[[result.best_index_]]

print(result_df["params"])

"""### Random Forest (with best parameters)"""

rf_classifier = RandomForestClassifier(n_estimators = 200, min_samples_split = 10, min_samples_leaf = 1, max_features = 'sqrt', max_depth = 30)
rf_classifier.fit(sem_tfidf_train, y_train)

pred = rf_classifier.predict(sem_tfidf_test)
print(classification_report(y_test, pred))

cm = metrics.confusion_matrix(y_test, pred, labels=['FALSE', 'TRUE', 'PARTIALLY FALSE', 'OTHER'])
print('Confusion Matrix: ')
print(cm)
plot_confusion_matrix(cm, classes=['FALSE', 'TRUE', 'PARTIALLY', 'OTHER'])

"""### Gradient Boosting (with default parameters)"""

gb_classifier = GradientBoostingClassifier(verbose=True, n_estimators = 200)
gb_classifier.fit(sem_tfidf_train, y_train)

pred = gb_classifier.predict(sem_tfidf_test)
print(classification_report(y_test, pred))

cm = metrics.confusion_matrix(y_test, pred, labels=['FALSE', 'TRUE', 'PARTIALLY FALSE', 'OTHER'])
print('Confusion Matrix: ')
print(cm)
plot_confusion_matrix(cm, classes=['FALSE', 'TRUE', 'PARTIALLY', 'OTHER'])

"""# Fourth Approach - Three-Layered Classification

## Data Preparation
"""

X = data.drop('our rating', axis = 1)
y = data['our rating']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.2, random_state = 42)

"""## Train and Test Splitting"""

X_train_text = X_train['clean_text']
X_test_text = X_test['clean_text']

X_train_POS = X_train['POS_text']
X_test_POS = X_test['POS_text']

X_train_sem = X_train['semantics_text']
X_test_sem = X_test['semantics_text']

"""### TFIDF"""

tfidf_vectorizer = TfidfVectorizer(stop_words='english', ngram_range = (1,3))
tfidf_train = tfidf_vectorizer.fit_transform(X_train_text.astype('str'))
tfidf_test = tfidf_vectorizer.transform(X_test_text.astype('str'))

tfidf_vectorizer = TfidfVectorizer(stop_words='english', ngram_range = (1,3))
tfidf_vectorizer.fit(X_train_text.astype('str'))

from sklearn import model_selection
import pickle

pickled_tfidf = 'tfidf_pickle.sav'
pickle.dump(tfidf_vectorizer, open(pickled_tfidf, 'wb'))

"""### POS Tagging"""

pos_tfidf_vectorizer = TfidfVectorizer(stop_words='english', ngram_range = (1,3))
pos_tfidf_train = pos_tfidf_vectorizer.fit_transform(X_train_POS.astype('str'))

pos_tfidf_test = pos_tfidf_vectorizer.transform(X_test_POS.astype('str'))

pos_tfidf_vectorizer = TfidfVectorizer(stop_words='english', ngram_range = (1,3))
pos_tfidf_vectorizer.fit(X_train_POS.astype('str'))

pickled_pos = 'pos_pickle.sav'
pickle.dump(pos_tfidf_vectorizer, open(pickled_pos, 'wb'))

"""### Semantic Analysis"""

sem_tfidf_vectorizer = TfidfVectorizer(stop_words='english', ngram_range = (1,1))
sem_tfidf_train = sem_tfidf_vectorizer.fit_transform(X_train_sem.astype('str'))

sem_tfidf_test = sem_tfidf_vectorizer.transform(X_test_sem.astype('str'))

sem_tfidf_vectorizer = TfidfVectorizer(stop_words='english', ngram_range = (1,1))
sem_tfidf_vectorizer.fit(X_train_sem.astype('str'))

pickled_sem = 'sem_pickle.sav'
pickle.dump(sem_tfidf_vectorizer, open(pickled_sem, 'wb'))

"""### Weight Setting"""

text_w = 0.5 * 3
pos_w = 0.15 * 3
sem_w = 0.35 * 3

tfidf_train *= text_w
tfidf_test *= text_w
pos_tfidf_train *= pos_w
pos_tfidf_test *= pos_w
sem_tfidf_train *= sem_w
sem_tfidf_test *= sem_w

diff_n_rows = pos_tfidf_train.shape[0] - tfidf_train.shape[0]
b = sp.vstack((tfidf_train, sp.csr_matrix((diff_n_rows, tfidf_train.shape[1]))))
c = sp.hstack((pos_tfidf_train, b))

diff_n_rows = c.shape[0] - sem_tfidf_train.shape[0]
b = sp.vstack((sem_tfidf_train, sp.csr_matrix((diff_n_rows, sem_tfidf_train.shape[1]))))

X_train = sp.hstack((c, b))

diff_n_rows = pos_tfidf_test.shape[0] - tfidf_test.shape[0]
d = sp.vstack((tfidf_test, sp.csr_matrix((diff_n_rows, tfidf_test.shape[1]))))
e = sp.hstack((pos_tfidf_test, d))

diff_n_rows = e.shape[0] - sem_tfidf_test.shape[0]
d = sp.vstack((sem_tfidf_test, sp.csr_matrix((diff_n_rows, sem_tfidf_test.shape[1]))))

X_test = sp.hstack((e, d))

"""## Model Testing

### Naive-Bayes Alpha-Tuning
"""

for alpha in alphas:
  print('Alpha: ', alpha)
  print('Score: ', train_and_predict(alpha, X_train, X_test))
  print()

"""### Naive-Bayes (with best parameters)"""

nb_classifier = MultinomialNB(alpha = 0.0)
nb_classifier.fit(X_train, y_train)

pred = nb_classifier.predict(X_test)
print(classification_report(y_test, pred))

cm = metrics.confusion_matrix(y_test, pred, labels=['FALSE', 'TRUE', 'PARTIALLY FALSE', 'OTHER'])
print('Confusion Matrix: ')
print(cm)
plot_confusion_matrix(cm, classes=['FALSE', 'TRUE', 'PARTIALLY', 'OTHER'])

"""### K Nearest Neighbors Hyper-Parameter Tuning"""

knn_params = RandomizedSearchCV(estimator=KNeighborsClassifier(), param_distributions={
    "leaf_size": list(range(1, 50)),
    "n_neighbors": list(range(1, 30)),
    "p": [1, 2]
}, n_iter=100, n_jobs=-1)

result = knn_params.fit(X_train, y_train)
result_df = pd.DataFrame(result.cv_results_).loc[[result.best_index_]]

print(result_df["params"])

"""### K Nearest Neighbors (with best parameters)"""

knn_classifier = KNeighborsClassifier(p = 2, n_neighbors = 19, leaf_size = 6)
knn_classifier.fit(X_train, y_train)

pred = knn_classifier.predict(X_test)
print(classification_report(y_test, pred))

cm = metrics.confusion_matrix(y_test, pred, labels=['FALSE', 'TRUE', 'PARTIALLY FALSE', 'OTHER'])
plot_confusion_matrix(cm, classes=['FALSE', 'TRUE', 'PARTIALLY', 'OTHER'])

"""### Random Forest Hyper-Parameter Tuning"""

rf_params = RandomizedSearchCV(estimator=RandomForestClassifier(), param_distributions={
    "n_estimators" : [200, 400, 600, 800, 1000],
    "max_features" : ['auto', 'sqrt'],
    "max_depth" : [10, 20, 30, 40, 50, None],
    "min_samples_split" : [2, 5, 10],
    "min_samples_leaf" : [1, 2, 4]
}, n_iter=10, n_jobs=-1)

result = rf_params.fit(X_train, y_train)
result_df = pd.DataFrame(result.cv_results_).loc[[result.best_index_]]

print(result_df["params"])

"""### Random Forest (with best parameters)"""

rf_classifier = RandomForestClassifier(n_estimators = 1000, min_samples_split = 10, min_samples_leaf = 2, max_features = 'auto', max_depth = 30)
rf_classifier.fit(X_train, y_train)

pred = rf_classifier.predict(X_test)
print(classification_report(y_test, pred))

cm = metrics.confusion_matrix(y_test, pred, labels=['FALSE', 'TRUE', 'PARTIALLY FALSE', 'OTHER'])
print('Confusion Matrix: ')
print(cm)
plot_confusion_matrix(cm, classes=['FALSE', 'TRUE', 'PARTIALLY', 'OTHER'])

"""### Gradient Boosting (with default parameters)"""

gb_classifier = GradientBoostingClassifier(verbose=True, n_estimators = 200)
gb_classifier.fit(X_train, y_train)

pred = gb_classifier.predict(X_test)
print(classification_report(y_test, pred))

cm = metrics.confusion_matrix(y_test, pred, labels=['FALSE', 'TRUE', 'PARTIALLY FALSE', 'OTHER'])
print('Confusion Matrix: ')
print(cm)
plot_confusion_matrix(cm, classes=['FALSE', 'TRUE', 'PARTIALLY', 'OTHER'])

gb_classifier = GradientBoostingClassifier(verbose=True, n_estimators = 200)
gb_classifier.fit(X_train, y_train)

pickled_model = 'three_layer_pickle.sav'
pickle.dump(gb_classifier, open(pickled_model, 'wb'))

loaded_model = pickle.load(open(pickled_model, 'rb'))
pred = loaded_model.predict(X_test)
print(classification_report(y_test, pred))

cm = metrics.confusion_matrix(y_test, pred, labels=['FALSE', 'TRUE', 'PARTIALLY FALSE', 'OTHER'])
print('Confusion Matrix: ')
print(cm)
plot_confusion_matrix(cm, classes=['FALSE', 'TRUE', 'PARTIALLY', 'OTHER'])