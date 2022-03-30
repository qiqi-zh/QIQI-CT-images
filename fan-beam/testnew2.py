import gc

import new2 as net
import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf
import os


def interp(f, xp, x):
    # f_img=f[:,:,::2,:]
    f_img = f
    shape = f.shape
    L = len(x)
    f_interp = np.zeros(shape=[shape[0], shape[1], L, shape[3]])
    idL = np.where(x <= xp[0])[0]
    idR = np.where(x >= xp[-1])[0]
    xx = x[idL[-1] + 1:idR[0]]
    id = np.searchsorted(xp, xx)
    L = xx - xp[id - 1]
    R = xp[id] - xx
    w1 = R / (L + R)
    w2 = 1 - w1
    val1 = f_img[:, :, id - 1, :]
    val2 = f_img[:, :, id, :]
    val1 = val1.transpose([0, 1, 3, 2])
    val2 = val2.transpose([0, 1, 3, 2])
    temp = val1 * w1 + val2 * w2
    f_interp[:, :, idL[-1] + 1:idR[0], :] = temp.transpose([0, 1, 3, 2])
    for i in idL:
        f_interp[:, :, i, :] = f_img[:, :, 0, :]
    for j in idR:
        f_interp[:, :, j, :] = f_img[:, :, -1, :]
    return f_interp


os.environ["CUDA_VISIBLE_DEVICES"] = "3"
L = 10
data = np.load('test' + '_fan_data.npz')


def mm():
    # AT = np.load('AT_fan_512x512_theta=0_0.5_175.5_alpha=-40:0.05:40_beta=0:1:359_R=600.npz')
    AT = np.load('../AT_fan_512x512_theta=0_0.5_175.5_alpha=-40_0.05_40_beta=0_1_359_R=600.npz')
    val = AT['val'].astype('float32')
    index = AT['index']
    shape = AT['shape']
    w_c = AT['w_c'].astype('float32')
    AT = tf.sparse.SparseTensor(index, val, shape)
    AT = tf.sparse.reorder(AT)  #######
    del val
    del index

    batch = 5
    s_shape = (360, 1601)
    out_size = (512, 512)
    max_alpha = 40
    n1 = 1601
    alpha = np.linspace(-max_alpha, max_alpha, n1) * np.pi / 180
    alpha = alpha.astype('float32')
    Model = net.make_model_3(AT, alpha, w_c, s_shape, out_size)
    # data = np.load('test' + '_fan_data.npz')
    f_noisy_img = data['sin_fan_ini'].astype('float32')
    # ckpt = './weights' + '/new2_model_lambda=0.5'
    L = 10
    f_noisy = f_noisy_img[0:L]

    prediction = evaluate(f_noisy, batch, Model)
    ii = np.random.randint(0, L)
    print('show figure:', ii)
    plt.imshow(f_noisy[ii, :, :, 0], cmap='gray')
    plt.show()
    plt.figure()
    plt.imshow(prediction[ii, :, :, 0], cmap='gray')
    plt.show()
    return prediction


def inimodel(f_noisy, Model):
    ckpt = './weights' + '/new2_model_lambda=0.5'
    _ = Model(f_noisy[0:1])
    Model.load_weights(ckpt)


def evaluate(f_noisy, batch, Model):
    _ = inimodel(f_noisy, Model)
    prediction = np.zeros([L, 512, 512, 1])
    iter = list(range(0, L, batch))
    for i in range(len(iter)):
        prediction[iter[i]:iter[i] + batch] = Model(f_noisy[iter[i]:iter[i] + batch])[1].numpy()
        print(i)
    return prediction



prediction = mm()
vy = data['u'].astype('float32')
del data
gc.collect()
vy = vy[0:L]
vy = tf.cast(vy, tf.float32)
pp = tf.image.psnr(tf.cast(prediction, tf.float32), vy, tf.reduce_max(prediction)).numpy()
qq = tf.image.ssim(tf.cast(prediction, tf.float32), vy, tf.reduce_max(prediction)).numpy()
print('average psnr:', tf.reduce_mean(pp).numpy())
print('average ssim:', tf.reduce_mean(qq).numpy())
