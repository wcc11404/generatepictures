import tensorflow as tf
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import os
from tensorflow.examples.tutorials.mnist import input_data

sess = tf.InteractiveSession()

mb_size = 128
Z_dim = 100

mnist = input_data.read_data_sets('../../MNIST_data', one_hot=True)

def weight_var(shape, name):
    return tf.get_variable(name=name, shape=shape, initializer=tf.contrib.layers.xavier_initializer())


def bias_var(shape, name):
    return tf.get_variable(name=name, shape=shape, initializer=tf.constant_initializer(0))


# discriminater net

X = tf.placeholder(tf.float32, shape=[None, 784], name='X')

D_W1 = weight_var([784, 128], 'D_W1')
D_b1 = bias_var([128], 'D_b1')

D_W2 = weight_var([128, 1], 'D_W2')
D_b2 = bias_var([1], 'D_b2')

theta_D = [D_W1, D_W2, D_b1, D_b2]


# generator net

Z = tf.placeholder(tf.float32, shape=[None, 100], name='Z')

G_W1 = weight_var([100, 128], 'G_W1')
G_b1 = bias_var([128], 'G_B1')

G_W2 = weight_var([128, 784], 'G_W2')
G_b2 = bias_var([784], 'G_B2')

keep_prob = tf.placeholder(tf.float32)

theta_G = [G_W1, G_W2, G_b1, G_b2]

def generator(z):
    G_h1 = tf.nn.relu(tf.matmul(z, G_W1) + G_b1)
    G_log_prob = tf.matmul(G_h1, G_W2) + G_b2
    G_prob = tf.nn.sigmoid(G_log_prob)


    return G_prob


def discriminator(x):
    D_h1 = tf.nn.relu(tf.matmul(x, D_W1) + D_b1)
    D_logit = tf.matmul(D_h1, D_W2) + D_b2
    D_prob = tf.nn.sigmoid(D_logit)
    D_drop = tf.nn.dropout(D_prob, keep_prob)  # dropout，keep_prob代表激活的神经元占总体的比例
    return D_drop, D_logit

#生成模型
G_sample = generator(Z)
#判别模型的真数据部分
D_real, D_logit_real = discriminator(X)
#判别模型的假数据部分
D_fake, D_logit_fake = discriminator(G_sample)      #如果weight和bias放在函数中定义，需要reuse,详情参见with tf.variable_scope()的用法

############两种loss计算方式########
#因为D_real和D_fake的输出只有1维，所以可以这样，否则用下边的loss计算方式，猜测
D_loss = -tf.reduce_mean(tf.log(D_real) + tf.log(1. - D_fake))
G_loss = -tf.reduce_mean(tf.log(D_fake))    #比起最小化tf.reduce_mean(1 - tf.log(D_fake))，最大化tf.reduce_mean(tf.log(D_fake))更好，论文说的

#reduce_mean取平均值，sigmoid_cross_entropy_with_logits先进行sigmoid函数，再求交叉熵
D_loss_real = tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(logits=D_logit_real, labels=tf.ones_like(D_logit_real)))
D_loss_fake = tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(logits=D_logit_fake, labels=tf.zeros_like(D_logit_fake)))
D_loss = D_loss_real + D_loss_fake
G_loss = tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(logits=D_logit_fake, labels=tf.ones_like(D_logit_fake)))
##################################

#优化方法用adam
D_optimizer = tf.train.AdamOptimizer().minimize(D_loss, var_list=theta_D)
G_optimizer = tf.train.AdamOptimizer().minimize(G_loss, var_list=theta_G)

#生成噪音数据
def sample_Z(m, n):
    '''Uniform prior for G(Z)'''
    return np.random.uniform(-1., 1., size=[m, n])

#绘图函数
def plot(samples):
    fig = plt.figure(figsize=(4, 4))
    gs = gridspec.GridSpec(4, 4)
    gs.update(wspace=0.05, hspace=0.05)

    for i, sample in enumerate(samples):  # [i,samples[i]] imax=16
        ax = plt.subplot(gs[i])
        plt.axis('off')
        ax.set_xticklabels([])
        ax.set_aspect('equal')
        plt.imshow(sample.reshape(28, 28), cmap='Greys_r')

    return fig

if not os.path.exists('out1/'):
    os.makedirs('out1/')

i = 0

#初始化变量
sess.run(tf.initialize_all_variables())
for it in range(1000000):
    if it % 1000 == 0:
        samples = sess.run(G_sample, feed_dict={Z: sample_Z(16, Z_dim),keep_prob:1.0})  # 16*784
        fig = plot(samples)
        plt.savefig('out1/{}.png'.format(str(i).zfill(3)), bbox_inches='tight')
        i += 1
        plt.close(fig)

    #取一个batch的数据
    X_mb, _ = mnist.train.next_batch(mb_size)   #y值也就是label写死在前文的代码中了

    _, D_loss_curr = sess.run([D_optimizer, D_loss], feed_dict={X: X_mb, Z: sample_Z(mb_size, Z_dim),keep_prob:0.5})#调用D_optimizer相当于一次前馈和反馈，D_loss调用只是前馈
    _, G_loss_curr = sess.run([G_optimizer, G_loss], feed_dict={Z: sample_Z(mb_size, Z_dim),keep_prob:0.5})

    if it % 1000 == 0:
        print('Iter: {}'.format(it))
        print('D loss: {:.4}'.format(D_loss_curr))
        print('G_loss: {:.4}'.format(G_loss_curr))
        print()