from sklearn.datasets import load_breast_cancer
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import numpy as np
import pandas as pd
from keras.datasets import cifar10
import matplotlib.pyplot as plt
import seaborn as sns

breast = load_breast_cancer()
breast_data = breast.data
breast_labels = breast.target

labels = np.reshape(breast_labels, (569, 1))
final_breast_data = np.concatenate([breast_data, labels], axis=1)

breast_dataset = pd.DataFrame(final_breast_data)
features = breast.feature_names
features_labels = np.append(features, 'label')
breast_dataset.columns = features_labels
breast_dataset['label'].replace(0, 'Benign', inplace=True)
breast_dataset['label'].replace(1, 'Malignant', inplace=True)

(x_train, y_train), (x_test, y_test) = cifar10.load_data()

# Find the unique numbers from the train labels
classes = np.unique(y_train)
nClasses = len(classes)
print('Total number of outputs : ', nClasses)
print('Output classes : ', classes)

label_dict = {
    0: 'airplane',
    1: 'automobile',
    2: 'bird',
    3: 'cat',
    4: 'deer',
    5: 'dog',
    6: 'frog',
    7: 'horse',
    8: 'ship',
    9: 'truck',
}

plt.figure(figsize=[5, 5])

# Display the first image in training data
plt.subplot(121)
curr_img = np.reshape(x_train[0], (32, 32, 3))
plt.imshow(curr_img)
print(plt.title("(Label: " + str(label_dict[y_train[0][0]]) + ")"))

# Display the first image in testing data
plt.subplot(122)
curr_img = np.reshape(x_test[0], (32, 32, 3))
plt.imshow(curr_img)
print(plt.title("(Label: " + str(label_dict[y_test[0][0]]) + ")"))

x = breast_dataset.loc[:, features].values
x = StandardScaler().fit_transform(x)  # normalizing the features

# Converting normalized data into tabular format
feat_cols = ['feature' + str(i) for i in range(x.shape[1])]
normalised_breast = pd.DataFrame(x, columns=feat_cols)

# Projecting the thirty-dimensional Breast Cancer data to two-dimensional components
pca_breast = PCA(n_components=2)
principalComponents_breast = pca_breast.fit_transform(x)

# Creating a dataFrame that will have the PCA values for all 569 samples
principal_breast_Df = pd.DataFrame(data=principalComponents_breast,
                                   columns=['principal component 1', 'principal component 2'])

# Prints explained_variance_ratio
print('Explained variation per principal component: {}'.format(pca_breast.explained_variance_ratio_))

# Plotting the visualizations of the 569 samples along the two PCA axes
plt.figure()
plt.figure(figsize=(10, 10))
plt.xticks(fontsize=12)
plt.yticks(fontsize=14)
plt.xlabel('Principal Component - 1', fontsize=20)
plt.ylabel('Principal Component - 2', fontsize=20)
plt.title("Principal Component Analysis of Breast Cancer Dataset", fontsize=20)
targets = ['Benign', 'Malignant']
colors = ['r', 'g']
for target, color in zip(targets, colors):
    indicesToKeep = breast_dataset['label'] == target
    plt.scatter(principal_breast_Df.loc[indicesToKeep, 'principal component 1'], principal_breast_Df.loc[indicesToKeep,
        'principal component 2'], c=color, s=50)

plt.legend(targets, prop={'size': 15})

# VISUALIZING THE CIFAR-10 DATA

# Checking min's and max's and normalizing the data to be between 0 and 1 inclusive

np.min(x_train), np.max(x_train)
x_train = x_train / 255.0

# Using DataFrame to hold the pixel values of the images along with their respective labels
# in a row-column format and shaping the image dimensions from 3 to 1 (flattening them)

x_train_flat = x_train.reshape(-1, 3072)
feat_cols = ['pixel' + str(i) for i in range(x_train_flat.shape[1])]
df_cifar = pd.DataFrame(x_train_flat, columns=feat_cols)
df_cifar['label'] = y_train
print('Size of the dataframe: {}'.format(df_cifar.shape))

# Creating PCA method to reduce dimensionality
pca_cifar = PCA(n_components=2)
principalComponents_cifar = pca_cifar.fit_transform(df_cifar.iloc[:, :-1])

# Convert the PCAs into numpy array to a pandas DataFrame
principal_cifar_Df = pd.DataFrame(data=principalComponents_cifar
                                  , columns=['principal component 1', 'principal component 2'])
principal_cifar_Df['y'] = y_train

print('Explained variation per principal component: {}'.format(pca_cifar.explained_variance_ratio_))

plt.figure(figsize=(16, 10))
sns.scatterplot(
    x="principal component 1", y="principal component 2",
    hue="y",
    palette=sns.color_palette("hls", 10),
    data=principal_cifar_Df,
    legend="full",
    alpha=0.3
)
