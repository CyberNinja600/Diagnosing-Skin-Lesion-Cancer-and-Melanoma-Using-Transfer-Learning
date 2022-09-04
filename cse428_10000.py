# -*- coding: utf-8 -*-
"""CSE428_10000.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1UNX0fFTLbCKogtYeYfow4vrW9fFKVj15
"""

import warnings
warnings.filterwarnings('ignore')

"""#**Import Libraries and Modules**"""

import numpy as np
import pandas as pd

import io
import os
import tensorflow as tf

from PIL import Image
from glob import glob
import itertools

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import seaborn as sns


import tensorflow as tf
from keras.callbacks import ReduceLROnPlateau
from keras.preprocessing.image import ImageDataGenerator
from tensorflow import keras
from tensorflow.keras.callbacks import ReduceLROnPlateau, EarlyStopping
from tensorflow.keras.layers import Conv2D, Flatten, BatchNormalization, Dropout, Dense, MaxPool2D,Dropout, Dot, RepeatVector
from tensorflow.keras.losses import categorical_crossentropy

from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, roc_curve

from IPython.display import display
from IPython.core.interactiveshell import InteractiveShell
InteractiveShell.ast_node_interactivity = "all"



"""#**Data Analysis**"""

base_skin_dir = '/content/drive/MyDrive/HAM2000'
#base_skin_dir = '/content/drive/MyDrive/HAM500'

# Merging images from both folders HAM10000_images_part1.zip and HAM10000_images_part2.zip into one dictionary

imageid_path_dict = {os.path.splitext(os.path.basename(x))[0]: x
                     for x in glob(os.path.join(base_skin_dir, '*', '*.jpg'))}
lesion_type_dict = {
    'nv': 'Melanocytic nevi (nv)',
    'mel': 'Melanoma (mel)',
    'bkl': 'Benign keratosis-like lesions (bkl)',
    'bcc': 'Basal cell carcinoma (bcc)',
    'akiec': 'Actinic keratoses (akiec)',
    'vasc': 'Vascular lesions (vasc)',
    'df': 'Dermatofibroma (df)'
}
label_mapping = {
    0: 'nv',
    1: 'mel',
    2: 'bkl',
    3: 'bcc',
    4: 'akiec',
    5: 'vasc',
    6: 'df'
}
reverse_label_mapping = dict((value, key) for key, value in label_mapping.items())

skin_df = pd.read_csv(os.path.join(base_skin_dir, 'HAM10000_metadata - HAM10000_metadata.csv'))

# Creating New Columns for better readability

skin_df['path'] = skin_df['image_id'].map(imageid_path_dict.get)
skin_df['cell_type'] = skin_df['dx'].map(lesion_type_dict.get) 
skin_df['cell_type_idx'] = pd.Categorical(skin_df['cell_type']).codes

"""#**Frequency of Each Class**

### **Bar graph representing lesions types**
"""

fig, ax1 = plt.subplots(1, 1, figsize= (10, 5))
skin_df['cell_type'].value_counts().plot(kind='bar', ax=ax1)

"""###**Frequency of DX_Type**

"""

skin_df['dx_type'].value_counts().plot(kind='bar')

"""### **Histogram of Affected Regions**"""

skin_df['localization'].value_counts().plot(kind='bar')

"""### **Histogram of Age Classes**"""

skin_df['age'].hist(bins=40)

"""### **Frequency of Sexes**"""

skin_df['sex'].value_counts().plot(kind='bar')

"""###Age-Cell_Type Scatter Plot"""

sns.scatterplot('age','cell_type_idx',data=skin_df)

"""###Sex-Cell_Type Factorplot"""

sns.factorplot('sex','cell_type_idx',data=skin_df)

from google.colab import drive
drive.mount('/content/drive')

"""#Data Processing"""

base_skin_dir = '/content/drive/MyDrive/HAM2000'
#base_skin_dir = '/content/drive/MyDrive/HAM500'

# Merging images from both folders HAM10000_images_part1.zip and HAM10000_images_part2.zip into one dictionary

imageid_path_dict = {os.path.splitext(os.path.basename(x))[0]: x
                     for x in glob(os.path.join(base_skin_dir, '*', '*.jpg'))}
lesion_type_dict = {
    'nv': 'Melanocytic nevi (nv)',
    'mel': 'Melanoma (mel)',
    'bkl': 'Benign keratosis-like lesions (bkl)',
    'bcc': 'Basal cell carcinoma (bcc)',
    'akiec': 'Actinic keratoses (akiec)',
    'vasc': 'Vascular lesions (vasc)',
    'df': 'Dermatofibroma (df)'
}
label_mapping = {
    0: 'nv',
    1: 'mel',
    2: 'bkl',
    3: 'bcc',
    4: 'akiec',
    5: 'vasc',
    6: 'df'
}
reverse_label_mapping = dict((value, key) for key, value in label_mapping.items())
#data = pd.read_csv('/content/drive/MyDrive/HAM500/HAM10000_metadata.csv')
data = pd.read_csv('/content/drive/MyDrive/HAM2000/HAM10000_metadata - HAM10000_metadata.csv')
data.head()

data.describe(exclude=[np.number])

"""###Check Null Values"""

print("Null found: ",end="")
data.isnull().any().sum()

"""###Replace Null with Mean"""

data['age'].fillna(value=int(data['age'].mean()), inplace=True)
# Converting dtype of age to int32
data['age'] = data['age'].astype('int32')
# Adding cell_type and image_path columns
data['cell_type'] = data['dx'].map(lesion_type_dict.get)
data['path'] = data['image_id'].map(imageid_path_dict.get)
data.head()

# Adding image pixels
data['image_pixel'] = data['path'].map(lambda x: np.asarray(Image.open(x).resize((224,224))))

data.head(5)

"""###Plot Sample Figures

"""

# Displaying 2 images for each label
sample_data = data.groupby('dx').apply(lambda df: df.iloc[:3, [9, 7]])
plt.figure(figsize=(28, 12))
for i in range(21):
    plt.subplot(3, 7, i+1 )
    plt.imshow(np.squeeze(sample_data['image_pixel'][i]))
    img_label = sample_data['cell_type'][i]
    plt.title(img_label)
    plt.axis("off")
plt.show();

data['label'] = data['dx'].map(reverse_label_mapping.get)
data = data.sort_values('label')
data = data.reset_index()

"""#Data Splitting (Train-80% : Test-20%) 


"""

# ORIGINAL DATA
# Converting image pixel columnm into required format
X_orig = data['image_pixel'].to_numpy()
X_orig = np.stack(X_orig, axis=0)
Y_orig = np.array(data.iloc[:, -1:])
print(X_orig.shape)
print(Y_orig.shape)

def prepare_for_train_test(X, Y):

    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, random_state=1)
    
    train_datagen = ImageDataGenerator(rescale = 1./255,
                                  rotation_range = 10,
                                  width_shift_range = 0.2,
                                  height_shift_range = 0.2,
                                  shear_range = 0.2,
                                  horizontal_flip = True,
                                  vertical_flip = True,
                                  fill_mode = 'nearest')
    train_datagen.fit(X_train)
    test_datagen = ImageDataGenerator(rescale = 1./255)
    test_datagen.fit(X_test)
    return X_train, X_test, Y_train, Y_test

X_train_orig, X_test_orig, Y_train_orig, Y_test_orig = prepare_for_train_test(X_orig, Y_orig)

"""#### CNN """

height, width = 224, 224
batch_size=64

def create_VGG19_Model():
  from tensorflow.keras.layers.experimental import preprocessing
  tf.keras.backend.clear_session()
  input_shape = (height, width, 3)
  base_model = tf.keras.applications.vgg19.VGG19(
      weights='imagenet', 
      include_top=False,
      input_shape=input_shape
  )
  base_model.trainable = False

  model_vgg19 = tf.keras.Sequential()
  model_vgg19.add(base_model)
  model_vgg19.add(tf.keras.layers.Flatten())
  model_vgg19.add(tf.keras.layers.Dense(units = 7 , activation='softmax'))

  return model_vgg19

##train model
def train_model(model, X_train, Y_train, EPOCHS=15):
    early_stop = EarlyStopping(monitor='val_loss', patience=10, verbose=1, 
                           mode='auto')
                               #, restore_best_weights=True)
    
    reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.1, patience=3, 
                              verbose=1, mode='auto')
    
    history = model.fit(X_train,
                        Y_train,
                        validation_split=0.2,
                        batch_size = 64,
                        epochs = EPOCHS,
                        callbacks = [reduce_lr, early_stop])
    return history

##Test Model
def test_model(model, X_test, Y_test):
    model_acc = model.evaluate(X_test, Y_test, verbose=0)[1]
    print("Test Accuracy: {:.3f}%".format(model_acc * 100))
    y_true = np.array(Y_test)
    y_pred = model.predict(X_test)
    y_pred = np.array(list(map(lambda x: np.argmax(x), y_pred)))
    clr = classification_report(y_true, y_pred, target_names=label_mapping.values())
    print(clr)
    
    sample_data = X_test[:15]
    plt.figure(figsize=(22, 12))
    for i in range(15):
        plt.subplot(3, 5, i + 1)
        plt.imshow(sample_data[i])
        plt.title(label_mapping[y_true[i][0]] + '|' + label_mapping[y_pred[i]])
        plt.axis("off")
    plt.show()

def plot_model_training_curve(history):
    fig = make_subplots(rows=1, cols=2, subplot_titles=['Model Accuracy', 'Model Loss'])
    fig.add_trace(
        go.Scatter(
            y=history.history['accuracy'], 
            name='train_acc'), 
        row=1, col=1)
    fig.add_trace(
        go.Scatter(
            y=history.history['val_accuracy'], 
            name='val_acc'), 
        row=1, col=1)
    fig.add_trace(
        go.Scatter(
            y=history.history['loss'], 
            name='train_loss'), 
        row=1, col=2)
    fig.add_trace(
        go.Scatter(
            y=history.history['val_loss'], 
            name='val_loss'), 
        row=1, col=2)
    fig.show()

VGG19 = create_VGG19_Model()
optimizer =  tf.keras.optimizers.Adam(learning_rate = 0.0001)
VGG19.compile(loss = 'sparse_categorical_crossentropy',
                 optimizer = optimizer,
                 metrics = ['accuracy'])
VGG19.summary()

"""## Training Data"""

X_train_orig, X_test_orig, Y_train_orig, Y_test_orig = prepare_for_train_test(X_orig, Y_orig)
VGG19_history = train_model(VGG19, X_train_orig, Y_train_orig, 15)

"""Results"""

test_model(VGG19, X_test_orig, Y_test_orig)

plot_model_training_curve(VGG19_history)