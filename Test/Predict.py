# -*- coding: utf-8 -*-
import os

import numpy as np
import tensorflow as tf
from PIL import Image

from Config.config import sample_conf


class TestError(Exception):
    pass


class TestBatch(object):

    def __init__(self, char_set, image_height, image_width, label_len):
        self.y_predict = None
        self.saver = None

        # 获得图片宽高和字符长度基本信息
        # 初始化变量
        # 图片尺寸
        self.image_height = image_height
        self.image_width = image_width
        # 验证码长度（位数）
        self.max_captcha = label_len
        # 验证码字符类别
        self.char_set = char_set
        self.char_set_len = len(char_set)

        # tf初始化占位符
        self.X = tf.placeholder(tf.float32, [None, image_height * image_width])  # 特征向量
        self.Y = tf.placeholder(tf.float32, [None, self.max_captcha * self.char_set_len])  # 标签
        self.keep_prob = tf.placeholder(tf.float32)  # dropout值
        self.w_alpha = 0.01
        self.b_alpha = 0.1

    @staticmethod
    def gen_captcha_text_image(img_path):
        # 文件
        captcha_image = Image.open(img_path)
        captcha_array = np.array(captcha_image)  # 向量化

        return captcha_array

    @staticmethod
    def convert2gray(img):
        """
        图片转为灰度图，如果是3通道图则计算，单通道图则直接返回
        :param img:
        :return:
        """
        if len(img.shape) > 2:
            r, g, b = img[:, :, 0], img[:, :, 1], img[:, :, 2]
            gray = 0.2989 * r + 0.5870 * g + 0.1140 * b
            return gray
        else:
            return img

    def text2vec(self, text):
        """
        转标签为oneHot编码
        :param text: str
        :return: numpy.array
        """
        text_len = len(text)
        if text_len > self.max_captcha:
            raise ValueError('验证码最长{}个字符'.format(self.max_captcha))

        vector = np.zeros(self.max_captcha * self.char_set_len)

        for i, ch in enumerate(text):
            idx = i * self.char_set_len + self.char_set.index(ch)
            vector[idx] = 1
        return vector

    def model(self):
        x = tf.reshape(self.X, shape=[-1, self.image_height, self.image_width, 1])
        # 卷积层1
        wc1 = tf.get_variable(name='wc1', shape=[3, 3, 1, 32], dtype=tf.float32,
                              initializer=tf.contrib.layers.xavier_initializer())
        bc1 = tf.Variable(self.b_alpha * tf.random_normal([32]))
        conv1 = tf.nn.relu(tf.nn.bias_add(tf.nn.conv2d(x, wc1, strides=[1, 1, 1, 1], padding='SAME'), bc1))
        conv1 = tf.nn.max_pool(conv1, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1], padding='SAME')
        conv1 = tf.nn.dropout(conv1, self.keep_prob)

        # 卷积层2
        wc2 = tf.get_variable(name='wc2', shape=[3, 3, 32, 64], dtype=tf.float32,
                              initializer=tf.contrib.layers.xavier_initializer())
        bc2 = tf.Variable(self.b_alpha * tf.random_normal([64]))
        conv2 = tf.nn.relu(tf.nn.bias_add(tf.nn.conv2d(conv1, wc2, strides=[1, 1, 1, 1], padding='SAME'), bc2))
        conv2 = tf.nn.max_pool(conv2, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1], padding='SAME')
        conv2 = tf.nn.dropout(conv2, self.keep_prob)

        # 卷积层3
        wc3 = tf.get_variable(name='wc3', shape=[3, 3, 64, 128], dtype=tf.float32,
                              initializer=tf.contrib.layers.xavier_initializer())
        bc3 = tf.Variable(self.b_alpha * tf.random_normal([128]))
        conv3 = tf.nn.relu(tf.nn.bias_add(tf.nn.conv2d(conv2, wc3, strides=[1, 1, 1, 1], padding='SAME'), bc3))
        conv3 = tf.nn.max_pool(conv3, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1], padding='SAME')
        conv3 = tf.nn.dropout(conv3, self.keep_prob)
        print(">>> convolution 3: ", conv3.shape)
        next_shape = conv3.shape[1] * conv3.shape[2] * conv3.shape[3]

        # 全连接层1
        wd1 = tf.get_variable(name='wd1', shape=[next_shape, 1024], dtype=tf.float32,
                              initializer=tf.contrib.layers.xavier_initializer())
        bd1 = tf.Variable(self.b_alpha * tf.random_normal([1024]))
        dense = tf.reshape(conv3, [-1, wd1.get_shape().as_list()[0]])
        dense = tf.nn.relu(tf.add(tf.matmul(dense, wd1), bd1))
        dense = tf.nn.dropout(dense, self.keep_prob)

        # 全连接层2
        wout = tf.get_variable('name', shape=[1024, self.max_captcha * self.char_set_len], dtype=tf.float32,
                               initializer=tf.contrib.layers.xavier_initializer())
        bout = tf.Variable(self.b_alpha * tf.random_normal([self.max_captcha * self.char_set_len]))
        y_predict = tf.add(tf.matmul(dense, wout), bout)
        return y_predict

    def init(self):
        self.y_predict = self.model()
        self.saver = tf.train.Saver()

    def predict(self, img_path):
        with tf.Session() as sess:
            test_image = self.gen_captcha_text_image(img_path)
            test_image = self.convert2gray(test_image)
            test_image = test_image.flatten() / 255
            self.saver.restore(sess, '..\\model\\')
            predict = tf.argmax(tf.reshape(self.y_predict, [-1, self.max_captcha, self.char_set_len]), 2)
            text_list = sess.run(predict, feed_dict={self.X: [test_image], self.keep_prob: 1.})
            predict_text = text_list[0].tolist()
            p_text = ""
            for p in predict_text:
                p_text += str(self.char_set[p])
        return p_text


def main():
    char_set = sample_conf["char_set"]
    tb = TestBatch(char_set, image_height=32, image_width=130, label_len=4)
    tb.init()
    return tb.predict(r'E:\System\Downloads\captchaCaptcha.png')


if __name__ == '__main__':
    print(main())
