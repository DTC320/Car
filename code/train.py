import os

from torch import nn,optim
import torch
from torch.utils.data import DataLoader
from dataloader import *
from net import *
from torchvision.utils import save_image
from tensorboardX import SummaryWriter
from unetpp import *
from utils.losses import hybrid_loss, CriterionStructuralKD, CrossEntropyLoss2d
from tqdm import tqdm

writer = SummaryWriter() #可视化
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(device)
weight_path = 'params/unet.pth'
data_path = '/Users/dongtianchi/Documents/DL_final/code/data/train_data'
save_path = 'train_image'


if __name__ == '__main__':
    co_transform = MyCoTransform(augment=True, height=256, width=256)  # 1024)
    data_loader = DataLoader(MyDataset(data_path, transform=co_transform), batch_size=8, shuffle=True)
    net = UNet(3, 9).to(device)
    # net = NestedUNet(3, 9).to(device)
    net.train()
    # if os.path.exists(weight_path):
    #     net.load_state_dict(torch.load(weight_path))
    #     print('successful load weight！')
    # else:
    #     print('not successful load weight')

    opt = optim.Adam(net.parameters())
    # loss_fun = hybrid_loss
    loss_fun = CrossEntropyLoss2d()

    epoch = 1
    epochs = 100

    for epoch in tqdm(range(1, epochs), desc='Processing'):
        running_loss = 0.0
        print('Epoch {}/{}'.format(epoch, epochs))
        for i, (image, segment_image, segment_name) in enumerate(data_loader):
            image, segment_image = image.to(device), segment_image.to(device)
            print('torch.unique(seg)', torch.unique(segment_image))
            out_image = net(image)  #out_image.shape = [2, 3, 256, 256]
            # train_loss = loss_fun(out_image, segment_image.long())
            segment_image = np.squeeze(segment_image, axis=1)
            train_loss = loss_fun(out_image[0], segment_image.long())

            opt.zero_grad()
            train_loss.backward()
            opt.step()
            running_loss += train_loss.data.item()
            epoch_loss = running_loss / epoch

            if i % 5 == 0:
                print(f'{epoch}-{i}-train_loss===>>{train_loss.item()}')

            # if i%10==0:
            #     _image = image[0]
                # _segment_image = torch.stack([segment_image[0], segment_image[0], segment_image[0]],dim=0)
                # # print('_segment_image.shape', _segment_image.shape)
                # _segment_image = torch.squeeze(_segment_image, 1)
                # # print('_segment_image1.shape', _segment_image.shape)
                # _out_image = torch.stack([out_image[0],out_image[0],out_image[0]],dim=0)
                # _out_image = torch.squeeze(_out_image, 1)
                # # print("++++++++++++++out_image:", _out_image)
                #
                # img = torch.stack([_image, _segment_image, _out_image],dim=0)
                # save_image(img,f'{save_path}/{i}.png')

            writer.add_scalar('data/trainloss', epoch_loss, epoch)

        if epoch % 5 == 0:
            torch.save(net.state_dict(), 'checkpoints/model_epoch_{}.pth'.format(epoch))
            print('checkpoints/model_epoch_{}.pth saved!'.format(epoch))

        epoch += 1

writer.close()
