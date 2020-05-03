
import os
import time
import numpy as np
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
import torch.optim as optim
import torchvision.datasets as dset
import torchvision.transforms as T
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torch.utils.data import sampler
from google.colab import drive
from glob import glob
from datetime import datetime
from PIL import Image
import random
import shutil
import csv
import math



class bn_relu_conv(nn.Module):
    def __init__(self, nin, nout, kernel_size, stride, padding, bias=False):
        super(bn_relu_conv, self).__init__()
        self.batch_norm = nn.BatchNorm2d(nin)
        self.relu = nn.ReLU(True)
        self.conv = nn.Conv2d(nin, nout, kernel_size=kernel_size, stride=stride, padding=padding, bias=bias)

    def forward(self, x):
        out = self.batch_norm(x)
        out = self.relu(out)
        out = self.conv(out)

        return out

class bottleneck_layer(nn.Sequential):
  def __init__(self, nin, growth_rate, drop_rate=0.2):    
      super(bottleneck_layer, self).__init__()
      
      self.add_module('conv_1x1', bn_relu_conv(nin=nin, nout=growth_rate*4, kernel_size=1, stride=1, padding=0, bias=False))
      self.add_module('conv_3x3', bn_relu_conv(nin=growth_rate*4, nout=growth_rate, kernel_size=3, stride=1, padding=1, bias=False))
     
      self.drop_rate = drop_rate
      
  def forward(self, x):
      bottleneck_output = super(bottleneck_layer, self).forward(x)
      if self.drop_rate > 0:
          bottleneck_output = F.dropout(bottleneck_output, p=self.drop_rate, training=self.training)
          
      bottleneck_output = torch.cat((x, bottleneck_output), 1)
      
      return bottleneck_output

class Transition_layer(nn.Sequential):
  def __init__(self, nin, theta=0.5):    
      super(Transition_layer, self).__init__()
      
      self.add_module('conv_1x1', bn_relu_conv(nin=nin, nout=int(nin*theta), kernel_size=1, stride=1, padding=0, bias=False))
      self.add_module('avg_pool_2x2', nn.AvgPool2d(kernel_size=2, stride=2, padding=0))


class DenseBlock(nn.Sequential):
  def __init__(self, nin, num_bottleneck_layers, growth_rate, drop_rate=0.2):
      super(DenseBlock, self).__init__()
                        
      for i in range(num_bottleneck_layers):
          nin_bottleneck_layer = nin + growth_rate * i
          self.add_module('bottleneck_layer_%d' % i, bottleneck_layer(nin=nin_bottleneck_layer, growth_rate=growth_rate, drop_rate=drop_rate))

class DenseNet(nn.Module):
    def __init__(self, growth_rate=12, num_layers=100, theta=0.5, drop_rate=0.2, num_classes=10):
        super(DenseNet, self).__init__()
        
        assert (num_layers - 4) % 6 == 0
        
     
        num_bottleneck_layers = (num_layers - 4) // 6
        
        self.dense_init = nn.Conv2d(3, growth_rate*2, kernel_size=3, stride=1, padding=1, bias=True)
       
        self.dense_block_1 = DenseBlock(nin=growth_rate*2, num_bottleneck_layers=num_bottleneck_layers, growth_rate=growth_rate, drop_rate=drop_rate)

      
        nin_transition_layer_1 = (growth_rate*2) + (growth_rate * num_bottleneck_layers) 
        self.transition_layer_1 = Transition_layer(nin=nin_transition_layer_1, theta=theta)
        
        self.dense_block_2 = DenseBlock(nin=int(nin_transition_layer_1*theta), num_bottleneck_layers=num_bottleneck_layers, growth_rate=growth_rate, drop_rate=drop_rate)

        nin_transition_layer_2 = int(nin_transition_layer_1*theta) + (growth_rate * num_bottleneck_layers) 
        self.transition_layer_2 = Transition_layer(nin=nin_transition_layer_2, theta=theta)
        
        self.dense_block_3 = DenseBlock(nin=int(nin_transition_layer_2*theta), num_bottleneck_layers=num_bottleneck_layers, growth_rate=growth_rate, drop_rate=drop_rate)
        
        nin_fc_layer = int(nin_transition_layer_2*theta) + (growth_rate * num_bottleneck_layers) 
      

        self.fc_layer = nn.Linear(int(nin_fc_layer), num_classes)
         
    def forward(self, x):
        dense_init_output = self.dense_init(x)
        dense_block_1_output = self.dense_block_1(dense_init_output)
        transition_layer_1_output = self.transition_layer_1(dense_block_1_output)
        
        dense_block_2_output = self.dense_block_2(transition_layer_1_output)
        transition_layer_2_output = self.transition_layer_2(dense_block_2_output)
        
        dense_block_3_output = self.dense_block_3(transition_layer_2_output)
        
        global_avg_pool_output = F.adaptive_avg_pool2d(dense_block_3_output, (1, 1))                
        global_avg_pool_output_flat = global_avg_pool_output.view(global_avg_pool_output.size(0), -1)

        output = self.fc_layer(global_avg_pool_output_flat)
        
        return output

def DenseNetBC_100_12():
    return DenseNet(growth_rate=12, num_layers=100, theta=0.5, drop_rate=0.2, num_classes=9)
