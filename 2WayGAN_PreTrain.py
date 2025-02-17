import torch.optim as optim
from torchvision.utils import save_image
from _datetime import datetime
from libs.compute import *
from libs.constant import *
# from libs.old_model import *
from libs.model import *
import os

if __name__ == "__main__":

    start_time = datetime.now()

    # delete old logs and create new logs
    if os.path.exists('./models/log/log_PreTraining.txt'):
        os.remove('./models/log/log_PreTraining.txt')
        os.mknod('./models/log/log_PreTraining.txt')
    if os.path.exists('./models/log/log_PreTraining_LossList.txt'):
        os.remove('./models/log/log_PreTraining_LossList.txt')
        os.mknod('./models/log/log_PreTraining_LossList.txt')

    # Creating generator and discriminator
    generator_xy = Generator()
    generator_yx = Generator()

    generator_xy = nn.DataParallel(generator_xy)
    generator_yx = nn.DataParallel(generator_yx)

    if torch.cuda.is_available():
        generator_xy.cuda(device=device)
        generator_yx.cuda(device=device)

    # Loading Training and Test Set Data
    trainLoader1, trainLoader2, trainLoader_cross, testLoader = data_loader()

    # MSE Loss and Optimizer
    criterion = nn.MSELoss()

    optimizer_g_xy = optim.Adam(generator_xy.parameters(), lr=LEARNING_RATE, betas=(BETA1, BETA2))
    optimizer_g_yx = optim.Adam(generator_yx.parameters(), lr=LEARNING_RATE, betas=(BETA1, BETA2))

    # GENERATOR PRE-TRAINING LOOP
    print("Pre-training loop starting")
    batches_done = 0
    running_loss = 0.0
    running_losslist = []
    learning_rate = LEARNING_RATE
    for epoch in range(NUM_EPOCHS_PRETRAIN):

        for param_group in optimizer_g_xy.param_groups:
            param_group['lr'] = adjustLearningRate(learning_rate, epoch_num=epoch, decay_rate=DECAY_RATE)

        for param_group in optimizer_g_yx.param_groups:
            param_group['lr'] = adjustLearningRate(learning_rate, epoch_num=epoch, decay_rate=DECAY_RATE)

        for i, (target, input) in enumerate(trainLoader1, 0):
            unenhanced_image = input[0]
            enhanced_image = target[0]
            x = Variable(unenhanced_image.type(Tensor_gpu))  # X
            y = Variable(enhanced_image.type(Tensor_gpu))  # Y

            optimizer_g_xy.zero_grad()
            y1 = generator_xy(x)  # X->Y'
            g1_loss = criterion(x, y1)
            g1_loss.backward(retain_graph=True)
            optimizer_g_xy.step()

            optimizer_g_yx.zero_grad()
            x1 = generator_yx(y)  # Y->X'
            g2_loss = criterion(y, x1)
            g2_loss.backward(retain_graph=True)
            optimizer_g_yx.step()

            # Print statistics
            g_loss = (g1_loss + g2_loss) / 2
            running_losslist.append(g_loss.item())

            f = open("./models/log/log_PreTraining.txt", "a+")
            f.write("[Epoch %d/%d] [Batch %d/%d] [G1 loss: %f] [G2 loss: %f]\n" % (
                epoch + 1, NUM_EPOCHS_PRETRAIN + 1, i + 1, len(trainLoader1), g1_loss.item(), g2_loss.item()))
            print("[Epoch %d/%d] [Batch %d/%d] [G1 loss: %f] [G2 loss: %f]\n" % (
                epoch + 1, NUM_EPOCHS_PRETRAIN + 1, i + 1, len(trainLoader1), g1_loss.item(), g2_loss.item()))
            f.close()

            # if i % 200 == 200:    # print every 200 mini-batches
            if i % 1 == 0:

                save_image(y1.data,
                           "./models/pretrain_images/xy/gan2_pretrain_%d_%d.png" % (epoch + 1, i + 1),
                           nrow=8,
                           normalize=True)
                torch.save(generator_xy.state_dict(),
                           './models/pretrain_checkpoint/xy/gan2_pretrain_' + str(epoch + 1) + '_' + str(
                               i + 1) + '_xy.pth')

                save_image(x1.data,
                           "./models/pretrain_images/yx/gan2_pretrain_%d_%d.png" % (epoch + 1, i + 1),
                           nrow=8,
                           normalize=True)
                torch.save(generator_yx.state_dict(),
                           './models/pretrain_checkpoint/yx/gan2_pretrain_' + str(epoch + 1) + '_' + str(
                               i + 1) + '_yx.pth')

    end_time = datetime.now()
    print(end_time - start_time)

    f = open("./models/log/log_PreTraining_LossList.txt", "w")
    for item in running_losslist:
        f.write('%f\n' % item)
    f.close()
