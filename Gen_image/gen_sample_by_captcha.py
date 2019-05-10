# -*- coding: UTF-8 -*-
"""
使用captcha lib生成验证码（前提：pip install captcha）
"""
from captcha.image import ImageCaptcha
import os
import random
import time


def gen_special_img(_text, file_path, _font_size):
    # 生成img文件
    generator = ImageCaptcha(width=width, height=height, font_sizes=_font_size)  # 指定大小
    img = generator.generate_image(_text)  # 生成图片
    img.save(file_path)  # 保存图片


if __name__ == '__main__':
    # 配置参数
    root_dir = "../sample/origin/"  # 图片储存路径
    image_suffix = "png"  # 图片储存后缀
    # characters = "0123456789"  # 图片上显示的字符集
    characters = "abcdefghijklmnopqrstuvwxyz"
    count = 20  # 生成多少张样本
    char_count = 4  # 图片上的字符数量

    # 设置图片高度和宽度
    width = 130
    height = 32

    # 设置字体大小
    font_size = (20, 21, 22)

    # 判断文件夹是否存在
    if not os.path.exists(root_dir):
        os.mkdir(root_dir)

    for i in range(count):
        text = ""
        for j in range(char_count):
            text += random.choice(characters)
        time_c = str(time.time()).replace(".", "")
        p = os.path.join(root_dir, "{}_{}.{}".format(text, time_c, image_suffix))
        gen_special_img(text, p, font_size)
