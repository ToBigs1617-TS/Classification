import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import tensorflow as tf
import keras
from PIL import Image
import os, glob
import os.path


size = (800, 400)   # define the size of input image


def get_img_array(img_path, size):

  '''Get Image Array
     Args
     - img_path : (local) path of save image
     - size(tuple) : the size of input image '''

  img = keras.preprocessing.image.load_img(img_path, color_mode='grayscale', target_size=size)   # PIL instance of size=(800, 400)
  array = keras.preprocessing.image.img_to_array(img)   # 3D Numpy array of size=(800, 400, 1) (channel is 1, since 'color_mode' is set as 'grayscale')
  array = np.expand_dims(array, axis=0)   # expand the shape of an array (array => batch) / final size=(1, 800, 400, 1)
  return array


def make_gradcam_heatmap(img_array, model, target_layer, pred_index=None):

  '''Make Grad-CAM heatmap for visualization purpose
     Args
     - img_array(array) : returned array from function 'get_image_array'
     - model : classification model
     - target_layer(str) : name of last convolutional layer'''
  
  # Create a model('grad_model' below)
  # 1. The model maps the input image to the activations of the target layer
  # 2. It also maps the input image to the output predictions
  grad_model = tf.keras.models.Model(
        [model.inputs], [model.get_layer(target_layer).output, model.output]
    )
  
  # Compute the gradient for the predicted class, with respect to the activations of the target layer
  with tf.GradientTape() as tape:
    target_layer_output, preds = grad_model(img_array)
    if pred_index is None:
      pred_index = tf.argmax(preds[0])
    class_channel = preds[:, pred_index]
  
  grads = tape.gradient(class_channel, target_layer_output)   # gradient of the output neuron
  pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))   # vector, where each entry represents the mean intensity of gradient

  # Multiply each channel in the feature map array & Sum all the channels
  target_layer_output = target_layer_output[0]
  heatmap = target_layer_output @ pooled_grads[..., tf.newaxis]
  heatmap = tf.squeeze(heatmap)
  
  heatmap = tf.maximum(heatmap, 0) / tf.math.reduce_max(heatmap)   # Heatmap Normalization (0~1)
  return heatmap.numpy()


def path_array(type): 

  '''Return list of input image path
  Arg
  - type(str) : to load data from specific type folder'''
  
  path_array = []
  folder = os.listdir('input image path/'+str(type)+'/')
  for file in folder:
    path_array.append('input image path/'+str(type)+'/'+f'{file}')
  return path_array


def show_heatmap(model, path_array):
  '''
  Heatmap Visualization
  Args
  - model : classification model
  - path_array(iterable object) : input image path
  '''
  for i in range(len(path_array)):
    img_path = path_array[i]
    img_array = get_img_array(img_path, size=size)
    model.layers[-1].activation = None   # remove last layer's softmax
    heatmap = make_gradcam_heatmap(img_array, model, target_layer)
    plt.matshow(heatmap)
    plt.show()
