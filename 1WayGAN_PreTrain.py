import torch.optim as optim
from torchvision.utils import save_image
from _datetime import datetime
from libs.compute import *
from libs.constant import *
from libs.model import *

if __name__ == "__main__":

    start_time = datetime.now()

    learning_rate = LEARNING_RATE

    # Creating generator and discriminator
    generator = Generator()

    generator = nn.DataParallel(generator)

    if torch.cuda.is_available():
        generator.cuda(device=device)

    # Loading Training and Test Set Data
    trainLoader1, trainLoader2, trainLoader_cross, testLoader = data_loader()

    ### MSE Loss and Optimizer
    criterion = nn.MSELoss()

    optimizer_g = optim.Adam(generator.parameters(), lr=LEARNING_RATE, betas=(BETA1, BETA2))

    ### GENERATOR PRE-TRAINING LOOP
    print("Pre-training loop starting")
    batches_done = 0
    running_loss = 0.0
    running_losslist = []
    for epoch in range(NUM_EPOCHS_PRETRAIN):

        for param_group in optimizer_g.param_groups:
                    param_group['lr'] = adjustLearningRate(learning_rate, epoch_num=epoch, decay_rate=DECAY_RATE)

        for i, (target, input) in enumerate(trainLoader1, 0):
            unenhanced_image = input[0]
            enhanced_image = target[0]
            unenhanced = Variable(unenhanced_image.type(Tensor_gpu))
            enhanced = Variable(enhanced_image.type(Tensor_gpu))

            optimizer_g.zero_grad()

            generated_enhanced_image = generator(enhanced)
            loss = criterion(unenhanced, generated_enhanced_image)
            loss.backward(retain_graph=True)
            optimizer_g.step()

            # Print statistics
            running_loss += loss.item()
            running_losslist.append(loss.item())
            f = open("./models/log/log_PreTraining.txt", "a+")
            f.write("[Epoch %d/%d] [Batch %d/%d] [G loss: %f]\n" % (
                epoch + 1, NUM_EPOCHS_PRETRAIN + 1, i + 1, len(trainLoader1), loss.item()))
            f.close()
            # if i % 200 == 200:    # print every 200 mini-batches
            if i % 1 == 0:
                print('[%d, %5d] loss: %.5f' % (epoch + 1, i + 1, running_loss / 5))
                running_loss = 0.0
                save_image(generated_enhanced_image.data,
                           "./models/pretrain_images/1Way/gan1_pretrain_%d_%d.png" % (epoch + 1, i + 1),
                           nrow=8,
                           normalize=True)
                torch.save(generator.state_dict(),
                           './models/pretrain_checkpoint/1Way/gan1_pretrain_' + str(epoch + 1) + '_' + str(i + 1) + '.pth')

    end_time = datetime.now()
    print(end_time-start_time)

    f = open("./models/log/log_PreTraining_LossList.txt", "a+")
    for item in running_losslist:
        f.write('%f\n' % item)
    f.close()
