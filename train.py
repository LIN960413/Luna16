import torch
import numpy as np
import time
import os
from model.net import Net
from model.loss import Loss
from torch.autograd import Variable

TOTAL_EPOCHS = 100
DEFAULT_LR = 0.01


def get_lr(epoch):
    if epoch <= TOTAL_EPOCHS * 0.5:
        lr = DEFAULT_LR
    elif epoch <= TOTAL_EPOCHS * 0.8:
        lr = 0.1 * DEFAULT_LR
    else:
        lr = 0.01 * DEFAULT_LR
    return lr


def train(data_loader, net, loss, epoch, optimizer, get_lr, save_dir='./'):
    start_time = time.time()

    net.train()
    lr = get_lr(epoch)
    for param_group in optimizer.param_groups:
        param_group['lr'] = lr

    metrics = []
    for i, (data, target, coord) in enumerate(data_loader):
        data = Variable(data.cuda())
        target = Variable(target.cuda())
        coord = Variable(coord.cuda())

        output = net(data, coord)
        loss_output = loss(output, target)
        optimizer.zero_grad()
        loss_output[0].backward()
        optimizer.step()

        loss_output[0] = loss_output[0].data[0]
        metrics.append(loss_output)

    if epoch % 10 == 0:
        state_dict = net.module.state_dict()
        for key in state_dict.keys():
            state_dict[key] = state_dict[key].cpu()
        torch.save({
            'epoch': epoch,
            'save_dir': save_dir,
            'state_dict': state_dict}, os.path.join(save_dir, f'''{epoch}.ckpt'''))

    end_time = time.time()

    metrics = np.asarray(metrics, np.float32)
    print(f'''Epoch {epoch} (lr {lr})''')
    print(f'''Train: tpr {100.0 * np.sum(metrics[:, 6]) / np.sum(metrics[:, 7])},
            tnr {100.0 * np.sum(metrics[:, 8]) / np.sum(metrics[:, 9])}, 
            total pos {np.sum(metrics[:, 7])}, total neg {np.sum(metrics[:, 9])}, 
            time {end_time - start_time}''')
    print(f'''loss {np.mean(metrics[:, 0])}, classify loss {np.mean(metrics[:, 1])},
            regress loss {np.mean(metrics[:, 2])}, {np.mean(metrics[:, 3])}, 
            {np.mean(metrics[:, 4])}, {np.mean(metrics[:, 5])}''')


def validate(data_loader, net, loss):
    start_time = time.time()

    net.eval()

    metrics = []
    for i, (data, target, coord) in enumerate(data_loader):
        data = Variable(data.cuda())
        target = Variable(target.cuda())
        coord = Variable(coord.cuda())

        output = net(data, coord)
        loss_output = loss(output, target, train=False)

        loss_output[0] = loss_output[0].data[0]
        metrics.append(loss_output)
    end_time = time.time()

    metrics = np.asarray(metrics, np.float32)
    print(f'''Validation: tpr {100.0 * np.sum(metrics[:, 6]) / np.sum(metrics[:, 7])},
            tnr {100.0 * np.sum(metrics[:, 8]) / np.sum(metrics[:, 9])}, 
            total pos {np.sum(metrics[:, 7])}, total neg {np.sum(metrics[:, 9])}, 
            time {end_time - start_time}''')
    print(f'''loss {np.mean(metrics[:, 0])}, classify loss {np.mean(metrics[:, 1])},
            regress loss {np.mean(metrics[:, 2])}, {np.mean(metrics[:, 3])}, 
            {np.mean(metrics[:, 4])}, {np.mean(metrics[:, 5])}''')


neural_net = Net()
loss_fn = Loss()
optim = torch.optim.SGD(
    neural_net.parameters(),
    DEFAULT_LR,
    momentum=0.9,
    weight_decay=1e-4)

for ep in range(TOTAL_EPOCHS):
    train(train_loader, neural_net, loss_fn, ep, optim, get_lr)
    validate(val_loader, neural_net, loss_fn)