import tensorflow as tf
from tensorflow.keras import layers, models
import matplotlib.pyplot as plt
import numpy as np
import os
from sklearn.utils import class_weight
# Dataset directory
data_dir = r"C:/Users/prema/OneDrive/Desktop/CDDM/PlantVillage"

# Image size and batch
IMG_SIZE = (180, 180)
BATCH_SIZE = 32





# Load training and validation datasets
train_ds = tf.keras.preprocessing.image_dataset_from_directory(
    data_dir,
    validation_split=0.2,
    subset="training",
    seed=123,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE
)

val_ds = tf.keras.preprocessing.image_dataset_from_directory(
    data_dir,
    validation_split=0.2,
    subset="validation",
    seed=123,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE
)

# Class names
class_names = train_ds.class_names
print("Classes:", class_names)

# Prefetching for performance
AUTOTUNE = tf.data.AUTOTUNE
train_ds = train_ds.prefetch(buffer_size=AUTOTUNE)
val_ds = val_ds.prefetch(buffer_size=AUTOTUNE)

# Data augmentation
data_augmentation = tf.keras.Sequential([
    layers.RandomFlip("horizontal_and_vertical"),
    layers.RandomRotation(0.2),
    layers.RandomZoom(0.2),
    layers.RandomContrast(0.1)
])

# Load MobileNetV2 as base model
base_model = tf.keras.applications.MobileNetV2(
    input_shape=(180, 180, 3),
    include_top=False,
    weights='imagenet'
)
base_model.trainable = False  # Freeze the base model

# Build final model
model = models.Sequential([
    data_augmentation,
    layers.Rescaling(1./255),
    base_model,
    layers.GlobalAveragePooling2D(),
    layers.Dropout(0.3),
    layers.Dense(128, activation='relu'),
    layers.Dropout(0.2),
    layers.Dense(len(class_names), activation='softmax')
])

# Compile model
model.compile(
    optimizer=tf.keras.optimizers.Adam(),
    loss='sparse_categorical_crossentropy',
    metrics=['accuracy']
)

# Callbacks
early_stop = tf.keras.callbacks.EarlyStopping(patience=5, restore_best_weights=True)
lr_reduce = tf.keras.callbacks.ReduceLROnPlateau(factor=0.2, patience=3)



# Extract labels from training dataset
labels = []
for _, batch_labels in train_ds.unbatch():
    labels.append(batch_labels.numpy())

labels = np.array(labels)

# Compute weights
class_weights = class_weight.compute_class_weight(
    class_weight='balanced',
    classes=np.unique(labels),
    y=labels
)

# Convert to dictionary
class_weights_dict = dict(enumerate(class_weights))
print("Class Weights:", class_weights_dict)




# Train model

history = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=15,
    callbacks=[early_stop, lr_reduce],
    class_weight=class_weights_dict  # 👈 this handles imbalance
)


# Save model and class names
model.save("crop_disease_model_mobilenetv2.h5")
with open("class_names_mobilenetv2.txt", "w") as f:
    for name in class_names:
        f.write(name + "\n")
