
import os
import time
import json
import shutil
import importlib
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
from glob import glob
from datetime import datetime
from PIL import Image

# import backup
import TUE_5LSM0_g6.backup
importlib.reload(TUE_5LSM0_g6.backup)
backup = TUE_5LSM0_g6.backup.backup

# constants
N_classes = 9
N_train = 22799
N_val = 2532
N_test = 8238


# ---------------------------------------------------------------------------- #

class Train():
  
  def init(self, model, model_data, optimizer, dataloader, dl_val, lr_exp, S):
    """
    Trains the specified model and prints the progress
    
    Args:
      model (torch.nn.Module):  model
      optimizer (torch.optim.Optimizer): optimizer
      epochs (int): number of epochs to train the model

    Returns:
      (none)
    """

    # sanity check
    if not isinstance(model, torch.nn.Module):
      raise TypeError('model must be of type torch.nn.Module')
    if not isinstance(model_data, dict):
      raise InstanceError('model_data needs to be a dictionary')

    # create validation score object
    val_score = Score(model)

    # add keys to dictionary if its empty and restore val-score otherwise.
    if not model_data:
      model_data['loss'] = []
      model_data['time_elapsed'] = []
      model_data['validation_score'] = []
    else:
      val_score.restore(model_data['validation_score'])

    
    # set class attributes
    if not len(model.validation_score.epoch) == 0
      self.epochs = model.validation_score.epoch[-1] + 1 + np.arange(S.epochs)
      self.iteration = model.validation_score.iteration[-1]
    else
      self.epochs = 1 + np.arange(S.epochs)
      self.iteration = 0
    self.iter_per_epoch = int( np.ceil( N_train / S.batch_size  ) )
    self.prints_per_epoch = selfiter_per_epoch // S.evaluate_every
    self.epoch_end = epochs[-1]
    self.iteration_start = self.iteration
    self.iteration_end = self.epoch_end * self.iter_per_epoch

    # move model to cpu/gpu
    model = model.to(device=S.device)  # move the model parameters to CPU/GPU

    # start timer
    self.time_start = time.clock()

    # start (or resume) training
    print('\nEstimated number of iterations per epoch: %i\n' % self.iter_per_epoch)
    for e in epochs:
      self.cur_print = 0
      for t, (x, y) in enumerate(dataloader):

        # update current iteration and epoch
        self.iteration += 1
        self.epoch = e

        # put model to training mode and move (x,y) to cpu/gpu
        model.train()  
        x = x.to(device=S.device, dtype=S.dtype)
        y = y.to(device=S.device, dtype=torch.long)

        # calculate scores
        scores = model(x)

        # calculate loss(cross etnropy)
        loss = F.cross_entropy(scores, y)
        
        # Zero out all of the gradients for the variables which the optimizer
        # will update.
        optimizer.zero_grad()

        # backward pass, compute loss gradient
        loss.backward()

        # update parameters using gradients
        optimizer.step()
        
        # evaluate model on validation data and print (part of) the results.
        if t % S.evaluate_every == 0:
          self.cur_print += 1
          self._evaluate_and_print(model, time_start, loss)


        # append loss 
        model.loss.append(loss)

      # bakcup model (if required)
      if S.backup_each_epoch:
        backup2(model)

      # update learning rate
      lr_exp.step()
      print('\n new lr = ', lr_exp.get_lr())


  # ---------------------------------------------------------------------------- #
  def _evaluate_and_print(model, time_start, loss):

    # evaluate (bma: balanced multiclass accuracy)
    bma, tp, p = model.score.calculate(self.epoch, self.iteration)
    t_elap = time.clock() - self.time_start
    t_per_iter = t_elap / (self.iteration - self.iteration_start)
    t_rem = (self.iteration_end - self.iteration) * t_per_iter

    # print
    #   line 1
    var1 = 'Epoch %i/%i ' % (self.epoch, self.epoch_end)
    var2 = 'print %i/%i ' % (self.cur_print, self.prints_per_epoch)
    var3 = 't_elaps.%s t_rem.%s ' %  (time_str(t_elap), time_str(t_rem))
    var4 = 'loss %.4f ' % loss.item()
    var5 = 'bma %.2f ' % bma
    line1 = var1 + var2 + var3 + var4 + var5
    #   line 2 and 3
    line23 = '\t'
    label_names = dataloader.dataset.classes
    for label in range(N_classes):
      if label==4: # add line break
        line23 += '\n\t'
      elif ii==7: # skip class 'unk'
        continue
      line23 += '%-4s %5i/%-8i ' % (label_names[label] , tp[label], p[label] )
    #   print them
    print( line1 + line23 )

# ---------------------------------------------------------------------------- #
def time_str(t):
  return time.strftime('%Hh%Mm%Ss', time.gmtime(t))

# ---------------------------------------------------------------------------- #


