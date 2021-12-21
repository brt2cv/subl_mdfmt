#!/usr/bin/env python3
# @Date    : 2021-12-21
# @Author  : Bright Li (brt2@qq.com)
# @Link    : https://gitee.com/brt2
# @Version : 0.1.5

import os
import re
import datetime
import glob
from collections import defaultdict

from .md_parser import MarkdownParser, NullMarkdownFile
# from .util.imgfmt import png2jpg, resize

# def png2jpg_for_md(path_png):
#     """ 验证png转换后体积明显缩小，
#         否则添加前缀，避免修改后再次上传时重复进行格式转换 """
#     new_file_prefix="keepng_"
#     if os.path.basename(path_png).startswith(new_file_prefix):
#         return path_png

#     path_jpg = png2jpg(path_png, 85)
#     if path_jpg == path_png:
#         path_jpg = os.path.join(os.path.dirname(path_png),
#            new_file_prefix + os.path.basename(path_png))
#         os.rename(path_png, path_jpg)
#     return path_jpg

class MarkdownFormatter(MarkdownParser):

    def format(self, resize_imgs=False):
        # self._update_categories()

        if not self.check_list["find_TOC"]:
            toc_index = self.check_list["index_H2"]
            if toc_index is None:
                toc_index = 0
            self.insert_text(toc_index, "[TOC]\n\n---\n\n")

        if self.check_list["index_H1"]:
            self.pop_text(self.check_list["index_H1"])

        self.update_serial_num()
        self.update_description()
        self.update_meta()  # Front Matter

        # # 图像处理
        # if self.get_images("http") and input("是否尝试下载超链接图片？[Y/n]: ").lower() != "n":
        #     # self.unlock_text()
        #     self.download_img()

        # # 默认启用 png -> jpg
        # self.convert_png2jpg()

        # # 对于高分辨率图像进行压缩
        # if resize_imgs:
        #     self.resize_high_resolution()

        # # 判断下载图像的size，执行resize或压缩
        # self.compress_bigimg()

    def overwrite(self):
        with open(self.file_path, "w", encoding="utf8") as fp:
            fp.writelines(self.get_text())
        # print(f"Markdown文件已保存【{self.file_path}】")

    def _make_front_matter(self):
        def list_as_str(data: list):
            # str(data) -> 单引号，不符合markdown标准
            return "[\"" + "\",\"".join(data) + "\"]" if data else "[]"

        self.metadata["date"] = str(datetime.date.today())

        # date数据由于使用eval()反序列化，故必须使用""作为字符串
        str_md_info = """<!--
+++
title       = "{}"
description = "{}"
date        = "{}"
tags        = {}
categories  = {}
series      = {}
keywords    = {}
weight      = {}
toc         = true
draft       = false
+++ -->
""".format(self.metadata['title'], self.metadata['description'], self.metadata['date'],
    list_as_str(self.metadata.get('tags')), list_as_str(self.metadata.get('categories')),
    list_as_str(self.metadata.get('series')), list_as_str(self.metadata.get('keywords')),
    self.metadata['weight'])
        return str_md_info

    def update_meta(self):
        meta_line = self._make_front_matter()
        if self.meta_range[0] is not None:
        # def _remove_old_meta(self):
            __text_lines = self.get_text()
            meta_start, meta_end = self.meta_range
            if meta_start is not None:
                self.set_text(__text_lines[:meta_start] + __text_lines[meta_end +1:])

        # def _insert_meta(self):
            self.insert_text(0, meta_line)
            self.meta_range = [None, None]
        else:
            self.modify_text(0, meta_line)

    def update_serial_num(self):
        """ 使用3级序号：1.2.4. xxx """
        x, y, z = 0, 0, 0
        def get_serial():
            serial_num = ""
            for i in [x, y, z]:
                if i:
                    # print("__", serial_num, type(i))
                    serial_num += "{}.".format(i)
                else:
                    break
            return serial_num

        pattern_headline = re.compile(r"(#+) +(\d+\.\S*)? *(.*)")

        def update_line(line):
            serial_num = get_serial()
            # if self.check_list["has_serial_num"]:
            #     prefix, _, text = line.split(maxsplit=2)
            # else:
            #     prefix, text = line.split(maxsplit=1)
            prefix, _, text = re.match(pattern_headline, line).groups()
            return "{} {} {}".format(prefix, serial_num, text)

        self.head2 = []
        for index, line in enumerate(self.get_text()):
            if line.startswith("## "):
                x += 1
                y,z = 0,0

                new_line = update_line(line)
                self.modify_text(index, new_line)
                # h2 = re.match(pattern_headline, line).groups()[2]
                _, h2 = new_line.split(maxsplit=1)
                self.head2.append(h2)
            elif line.startswith("### "):
                y += 1
                z = 0
                self.modify_text(index, update_line(line))
            elif line.startswith("#### "):
                z += 1
                self.modify_text(index, update_line(line))

    def update_description(self):
        if not self.metadata['description']:
            self.metadata['description'] = "; ".join(self.head2)

    def download_img(self):
        from util.imgfmt import download_src

        dict_images = self.get_images("http")
        # 生成图像目录
        dir_img, _ = os.path.splitext(self.file_path)
        if not os.path.exists(dir_img):
            os.makedirs(dir_img)
        self.process_images(dict_images, lambda url: os.path.relpath(download_src(url, dir_img),
                                                            os.path.dirname(self.file_path)))

    def convert_png2jpg(self):
        dict_images = self.get_images("png")
        self.process_images(dict_images, lambda path_png: os.path.relpath(png2jpg_for_md(path_png),
                                                            os.path.dirname(self.file_path)))
        # 删除原png文件
        # for path_img in dict_images.values():
        #     os.remove(path_img)

    def compress_jpg(self):
        pass

    def compress_bigimg(self):
        pass

    # def resize_high_resolution(self, save_as_jpg=True):
    #     dict_images_png = self.get_images("png")
    #     dict_images_jpg = self.get_images("jpg")
    #     callback = lambda url: resize(url, ratio=0.6, min_size=10240,
    #                                   max_shape=[680,680], save_as_jpg=save_as_jpg)
    #     self.process_images({**dict_images_png, **dict_images_jpg}, callback)

#####################################################################

def getopt():
    import argparse

    parser = argparse.ArgumentParser("格式化mkdocs文档", description="")
    parser.add_argument("-p", "--path", action="store", help="解析文件路径，可以是文件或目录")
    return parser.parse_args()

def format_one_doc(fmt, path_file):
    fmt.load_file(path_file)
    fmt.format(resize_imgs=False)

def format_dir(fmt, path_dir):
    list_files = glob.glob("{}/**/*.md" % path_dir, recursive=True)

    err_files = defaultdict(list)
    for path_file in list_files:
        try:
            format_one_doc(fmt, path_file)
        except NullMarkdownFile:
            err_files["NullMarkdownFile"].append(path_file)

    if err_files:
        for key, list_files in err_files.items():
            print(">> 错误文件类型【{}】" % key)
            print("   文件列表： {}" % list_files)

def format_anything(fmt, path):
    if os.path.isdir(path):
        format_dir(fmt, path)
    else:
        format_one_doc(fmt, path)


if __name__ == "__main__":
    args = getopt()
    fmt = MarkdownFormatter()

    if args.path:
        format_anything(fmt, args.path)
    else:
        path = input("\n请输入待处理文件path(支持直接拖拽): ")
        while True:
            path = path.strip().strip('"')
            if os.path.exists(path):
                format_anything(fmt, path)
                fmt.overwrite()
            else:
                print("Error: File [{}] NOT found." % path)

            path = input("继续输入path，按[Q]退出: ")
            if path.lower() == "q":
                break
