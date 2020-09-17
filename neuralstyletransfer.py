# -*- coding: utf-8 -*-
"""NeuralStyleTransfer.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1OSJhvBVsXFmWvjU0KANe8jpV_ZplVvQL

##Importing Libraries
"""

import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
import torch
import torch.optim as optim
import torchvision.models as models
from torchvision import transforms as tf
import torch.nn.functional as F
from tqdm.notebook import tqdm_notebook
from PIL import ImageFile

"""## Loding VGG19 from Pytorch"""

vgg = models.vgg19(pretrained=True).features

for param in vgg.parameters():
    param.requires_grad_(False)

device = torch.device("cpu")

if torch.cuda.is_available():
    device = torch.device("cuda")
    
vgg.to(device)

"""## Defining Helper Functions"""

mean = (0.485, 0.456, 0.406)
std = (0.229, 0.224, 0.225)

def transformation(img):
    
    tasks = tf.Compose([tf.Resize(1024), 
                        tf.ToTensor(),
                        tf.Normalize(mean, std)])
    
    img = tasks(img)  
    img = img.unsqueeze(0)    
    
    return img

def tensor_to_image(tensor):

    image = tensor.clone().detach()
    image = image.cpu().numpy().squeeze()
    
    image = image.transpose(1, 2, 0)
    
    image = image * np.array(std) + np.array(mean)
    image = image.clip(0, 1)
    
    return image

"""## Load images"""


ImageFile.LOAD_TRUNCATED_IMAGES = False

content_img = Image.open("ex.JPG").convert('RGB')
style_img   = Image.open("2.jpg").convert('RGB')

content_img = transformation(content_img).to(device)
style_img   = transformation(style_img).to(device)


"""## Defining Layers of Interest"""

LAYERS_OF_INTEREST = {'0': 'conv1_1', 
                      '5': 'conv2_1',  
                      '10': 'conv3_1', 
                      '19': 'conv4_1', 
                      '21': 'conv4_2', 
                      '28': 'conv5_1'}

"""## Feature extraction for content and style images"""

def apply_model_and_extract_features(image, model):
    x = image

    features = {}
    
    for name, layer in model._modules.items():
        x = layer(x)
        
        if name in LAYERS_OF_INTEREST:
            features[LAYERS_OF_INTEREST[name]] = x   
            
    return features

content_img_features = apply_model_and_extract_features(content_img, vgg)
style_img_features   = apply_model_and_extract_features(style_img, vgg)

"""## Calculating gram matrix for style image"""

def calculate_gram_matrix(tensor):
    
    _, channels, height, width = tensor.size()
    
    tensor = tensor.view(channels, height * width)    
    
    gram_matrix = torch.mm(tensor, tensor.t())
    
    gram_matrix = gram_matrix.div(channels * height * width) 
    
    return gram_matrix

style_features_gram_matrix = {layer: calculate_gram_matrix(style_img_features[layer]) for layer in 
                                                    style_img_features}

weights = {'conv1_1': 1.0, 'conv2_1': 0.75, 'conv3_1': 0.35,
           'conv4_1': 0.25, 'conv5_1': 0.15}

"""## Defining target image(same as content image)"""

target = content_img.clone().requires_grad_(True).to(device)

optimizer = optim.Adam([target], lr=0.003)

plt.figure()

plt.imshow(tensor_to_image(target))

"""## Performimg Style Transfer"""

for i in tqdm_notebook(range(1, 20)):
    
    target_features = apply_model_and_extract_features(target, vgg)

    content_loss = F.mse_loss (target_features['conv4_2'], content_img_features['conv4_2'])
    
    style_loss = 0
    for layer in weights:
        
        target_feature = target_features[layer]

        target_gram_matrix = calculate_gram_matrix(target_feature)
        style_gram_matrix = style_features_gram_matrix[layer]
        
        layer_loss = F.mse_loss (target_gram_matrix, style_gram_matrix)
        layer_loss *= weights[layer]
        
        _, channels, height, width = target_feature.shape

        style_loss += layer_loss  
    
    total_loss = 1000000 * style_loss + content_loss
    
    if i % 500 == 0:
        print ('Epoch {}:, Style Loss : {:4f}, Content Loss : {:4f}'.format( i, style_loss, content_loss))
    
    optimizer.zero_grad()
    
    total_loss.backward()
    
    optimizer.step()

"""## Results"""

fig, (ax1, ax2 , ax3) = plt.subplots(1, 3, figsize=(20, 10))
ax1.imshow(tensor_to_image(content_img))
ax2.imshow(tensor_to_image(style_img))
ax3.imshow(tensor_to_image(target))
plt.savefig('333.jpg')

