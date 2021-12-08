#!/usr/bin/env python3
# @Date    : 2020-08-04
# @Author  : Bright Li (brt2@qq.com)
# @Link    : https://gitee.com/brt2
# @Version : 1.0.3

import subprocess

def run_cmd(str_cmd):
    """ return a list stdout-lines """
    completed_process = subprocess.run(str_cmd,
                                shell=True,
                                check=True,
                                stdout=subprocess.PIPE)
    return completed_process.stdout.decode().splitlines()

def get_exif(path_jpg):
    stdout_ = run_cmd("jhead -se " + path_jpg)
    return stdout_

def remove_exif(path_jpg, forced=False):
    if forced:
        stdout_ = run_cmd("jhead -de " + path_jpg)
    else:
        stdout_ = run_cmd("jhead -purejpg " + path_jpg)
    return stdout_

def set_comment(path_jpg, comment):
    stdout_ = run_cmd("jhead -cl {} {}".format(comment, path_jpg))
    return stdout_

def clear_comment(path_jpg):
    stdout_ = run_cmd("jhead -dc " + path_jpg)
    return stdout_

def get_comment(path_jpg):
    stdout_ = run_cmd(r'jhead -se "%s"|grep Comment|awk "{print $3}" ' % path_jpg)
    if stdout_:
        return stdout_[0]

def get_resolution(path_jpg):
    stdout_ = run_cmd(r'jhead -se "%s"|grep Resolution ' % path_jpg)
    if stdout_:
        str_resolution = stdout_[0].split(": ")[1]
        return [int(x) for x in str_resolution.split(" x ")]

def get_size(path_jpg, unit="KB"):
    """ return an int-number of size by KB """
    # stdout_ = run_cmd(r"jhead -se %s|grep 'File size'" % path_jpg)
    # if not stdout_:
    #     return
    # str_size = stdout_[0].split(": ")[1]
    # unit_byte = int(str_size.split()[0])
    import os.path
    unit_byte = os.path.getsize(path_jpg)

    if unit == "B":
        return unit_byte
    elif unit == "KB":
        return unit_byte // 1024
    elif unit == "MB":
        return unit_byte // 1e6
    else:
        raise Exception("不支持的单位【{}】".format(unit))


if __name__ == "__main__":
    def getopt():
        import argparse

        parser = argparse.ArgumentParser("extract-exif", description="提取jpg图像的exif信息")
        parser.add_argument("path_jpg", action="store", help="图像路径")
        parser.add_argument("-c", "--comment", action="store_true", help="查看图像注释信息")
        parser.add_argument("-r", "--resolution", action="store_true", help="查看图像像素")
        parser.add_argument("-s", "--size", action="store_true", help="查看文件所占空间(KB)")
        return parser.parse_args()

    args = getopt()
    path_jpg = args.path_jpg

    if args.comment:
        print(get_comment(path_jpg))
    elif args.resolution:
        print(get_resolution(path_jpg))
    elif args.size:
        print(get_size(path_jpg), "KiB")
    else:
        print(get_exif(path_jpg))
