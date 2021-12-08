#!/usr/bin/env python3
# @Date    : 2021-11-02
# @Author  : Bright Li (brt2@qq.com)
# @Link    : https://gitee.com/brt2
# @Version : 0.1.9

import os
from logging import getLogger
logger = getLogger(__file__)

from PIL import Image

#####################################################################
# pcall@Version : 0.2.1
#####################################################################
import subprocess

if hasattr(subprocess, 'run'):
    __PY_VERSION_MINOR = 5  # 高于3.5
# except AttributeError:
else:
    __PY_VERSION_MINOR = 4  # 低于3.4

def _popen(str_cmd):
    completing_process = subprocess.Popen(str_cmd,
                                shell=True,
                                # stdin=subprocess.DEVNULL,
                                # stderr=subprocess.PIPE,
                                stdout=subprocess.PIPE)
    # stdout, stderr = completing_process.communicate()
    return completing_process


def pcall(str_cmd, block=True):
    ''' return a list stdout-lines '''
    if block:
        if __PY_VERSION_MINOR == 5:
            p = subprocess.run(str_cmd,
                                shell=True,
                                check=True,
                                stdout=subprocess.PIPE)
        else:
            p = subprocess.check_call(str_cmd,
                                shell=True)
        stdout = p.stdout
    else:
        p = _popen(str_cmd)
        stdout = p.communicate()  # timeout=timeout
    # rc = p.returncode
    return stdout.decode().splitlines()

#####################################################################
# end of pcall
#####################################################################


def _get_resolution_byPIL(path_img):
    # resolution = tuple()
    with Image.open(path_img) as img:
        resolution = img.size
    return resolution

# def get_size(path_file, unit="KB"):
#     unit_byte = os.path.getsize(path_file)

#     if unit == "KB":
#         return round(unit_byte / 1024, 2)
#     elif unit == "B":
#         return unit_byte
#     elif unit == "MB":
#         return round(unit_byte / 1e6, 2)
#     else:
#         raise Exception("不支持的单位【{}】".format(unit))

try:
    from jhead import size_density as size_density_byJhead
    from jhead import get_resolution as get_resolution_byJhead
except ImportError:
    #####################################################################
    # jhead@Version : 1.1.2
    #####################################################################
    def size_density_byJhead(path_jpg):
        """ 密度: 单位像素的空间占比，通过PIL压缩后的尺寸约为0.1-0.2 """
        # size = get_size(path_jpg, unit="B")
        stdout_ = pcall("jhead -se " + path_jpg)
        no_size = True
        for line in stdout_:
            if no_size:
                if line[:9] == "File size":
                    str_size = line.split(": ")[1]
                    size = int(str_size.split()[0])
                    no_size = False
            elif line[:10] == "Resolution":
                str_resolution = line.split(": ")[1]
                w, h = [int(x) for x in str_resolution.split(" x ")]
                n_pixel = w * h
                break
        ratio = size / n_pixel
        return ratio

    def get_resolution_byJhead(path_jpg):
        stdout_ = pcall(r'jhead -se "%s"|grep Resolution ' % path_jpg)
        if stdout_:
            str_resolution = stdout_[0].split(": ")[1]
            return [int(x) for x in str_resolution.split(" x ")]

    #####################################################################
    # end of jhead
    #####################################################################

def size_density(path_img):
    try:
        return size_density_byJhead(path_img)
    except subprocess.CalledProcessError:
        # size = get_size(path, unit="B")
        size = os.path.getsize(path_img)
        resolution = _get_resolution_byPIL(path_img)
        return size / (resolution[0] * resolution[1])

def size_resolution(path_img, thresh):
    """ thresh should be a tuple like (960, 480), and w >= h """
    try:
        w,h = get_resolution_byJhead(path_img)
    except (NameError, subprocess.CalledProcessError):
        w,h = _get_resolution_byPIL(path_img)
    if w < h:
        w, h = h, w
    return w <= thresh[0] and h <= thresh[1]

def filter_density(list_files, thresh=0.3):
    list_filters = []
    for path_img in list_files:
        if size_density(path_img) > thresh:
            list_filters.append(path_img)
    return list_filters


#####################################################################

import os.path

def resize(path_src, **kwargs):
    """
    kwargs:
        ratio: 缩放比例
        output_shape: list(w, h)
        min_size: 忽略存储空间小于此数值的小图片
        max_shape: 若为None，则正常缩放一次
                   否则递归压缩尺寸高于此数值的大图片, type: list(w, h)
        antialias: 开启抗锯齿（会增加图像的处理时长，默认开启）
        save_as_jpg: 强制将图像转换为jpg格式
    """
    default_kwargs = {
        "ratio": 0.5,
        "output_shape": None,
        "min_size": 0,
        "max_shape": None,
        "antialias": True,
        "save_as_jpg": True
    }
    default_kwargs.update(kwargs)
    kwargs = default_kwargs

    if os.path.getsize(path_src) < kwargs["min_size"]:
        return

    # 开启抗锯齿，耗时增加8倍左右
    resample = Image.ANTIALIAS if kwargs["antialias"] else Image.NEAREST

    im = Image.open(path_src)
    if im.mode == "RGBA" and kwargs["save_as_jpg"]:
        im = im.convert("RGB")

    if kwargs["output_shape"]:
        w, h = kwargs["output_shape"]
        im_new = im.resize((w, h), resample)
    elif kwargs["max_shape"] is None:  # 执行一次缩放
        # 注意：pillow.size 与 ndarray.size 顺序不同
        list_ = [int(i*kwargs["ratio"]) for i in im.size]
        im_new = im.resize(list_, resample)
    else:  # 递归缩减
        while True:
            w, h = im.size
            if w <= kwargs["max_shape"][0] and h <= kwargs["max_shape"][1]:
                break
            w, h = [int(i*kwargs["ratio"]) for i in im.size]
            im = im.resize((w, h), resample)
        im_new = im

    if kwargs["save_as_jpg"]:
        im_new.save(path_src, "JPEG", optimize=True, quality=85)
    else:
        im_new.save(path_src, optimize=True)

#####################################################################

def png2jpg_byMogrify(path_png):
    # sudo apt-get install imagemagick
    pcall("mogrify -format jpg {}".format(path_png))
    path_base, _ = os.path.splitext(path_png)
    return path_base + ".jpg"

def png2jpg_byPIL(path_png, path_new=None, quality=85):
    """ 转换png文件，并返回生成的jpg文件路径 """
    if not path_new:
        path_new = os.path.splitext(path_png)[0] + ".jpg"

    im = Image.open(path_png)  # rgba
    im_rgb = im.convert(mode="RGB")
    im_rgb.save(path_new, quality=quality)
    return path_new

def bmp2jpg_byPIL(path_bmp, path_new=None, quality=85, removeOrigin=True):
    """ 转换png文件，并返回生成的jpg文件路径 """
    if not path_new:
        path_new = os.path.splitext(path_bmp)[0] + ".jpg"

    im = Image.open(path_bmp)
    # im_rgb = im.convert(mode="RGB")
    im.save(path_new, quality=quality)
    del im

    if removeOrigin:
        os.remove(path_bmp)
    return path_new

bmp2jpg = bmp2jpg_byPIL

def bmp2png_byPIL(path_bmp, path_new=None, removeOrigin=True):
    """ 转换png文件，并返回生成的jpg文件路径 """
    if not path_new:
        path_new = os.path.splitext(path_bmp)[0] + ".png"

    im = Image.open(path_bmp)
    # im_rgb = im.convert(mode="RGB")
    im.save(path_new)
    del im

    if removeOrigin:
        os.remove(path_bmp)
    return path_new

bmp2png = bmp2png_byPIL

# def png_to_jpg_mask(pngPath, quality):
#     im = Image.open(pngPath)
#     r, g, b, a = im.convert(mode="RGBA").split()

#     name, _ = os.path.splitext(pngPath)
#     # jpgPath = name + ".jpg"
#     maskPath = name + ".mask.jpg"

#     a.convert(mode="L")
#     a.save(maskPath)

#     im.save(im.convert(mode="RGB"), quality=quality)

# def jpg_mask_to_png(jpgPath, maskPath):
#     """ 将分开的两张图片合成原图 """
#     im_jpg = Image.open(jpgPath)
#     im_mask = Image.open(maskPath)

#     im_jpg.putalpha(im_mask)
#     im_jpg.save(jpgPath + ".png")

def png2jpg(path_png, path_new=None, quality=85, least_ratio=0.8, removePng=True):
    """ png2jpg_base()未考虑转换结果。
        png2jpg_ex()则对比转换结果，如果转换后文件变大了，则保留原png.
        为了避免下次重复转换png，文件名增加前缀 keepng_
    """
    path_jpg = png2jpg_byPIL(path_png, path_new, quality)
    if least_ratio is None:
        ret = path_jpg
    # 比较size: 除非显著压缩，否则保留原图像
    elif os.path.getsize(path_jpg) < os.path.getsize(path_png) * least_ratio:
        ret = path_jpg
    else:
        os.remove(path_jpg)
        removePng = False
        ret = path_png

    if removePng:
        os.remove(path_png)
    return ret

def webp2png_byDwebp(path_webp, path_new=None):
    if not path_new:
        path_new = os.path.splitext(path_webp)[0] + ".png"

    pcall("dwebp {} -o {}".format(path_webp, path_new))
    return path_new

def webp2jpg_byPIL(path_webp, path_new=None, quality=85):
    if not path_new:
        path_new = os.path.splitext(path_webp)[0] + ".jpg"

    im = Image.open(path_webp)  # rgba
    im.save(path_new, "JPEG", quality=quality)
    return path_new

def webp2jpg(path_webp, path_new=None, quality=85, removeWebp=True):
    webp2jpg_byPIL(path_webp, path_new, quality)
    if removeWebp:
        os.remove(path_webp)
    return path_new

#####################################################################

from io import BytesIO

def compress_byPIL(path_img, quality=80):
    """ 适用于jpg图像的压缩 """
    with open(path_img, "rb+") as fp:
        origin_data = fp.read()

        im, out = Image.open(BytesIO(origin_data)), BytesIO()
        im.save(out, format=im.format, optimize=True, quality=quality)
        compressed_data = out.getvalue()

        compression_ratio = len(compressed_data) / len(origin_data)
        logger.debug(">>> PIL图像压缩比率: {}".format(compression_ratio))
        if compression_ratio < ImageCompressProcess.COMPRESS_RATIO_ALLOWED:
            fp.seek(0)
            fp.truncate()
            fp.write(compressed_data)
    return compression_ratio

compress_jpeg = compress_byPIL

class ImageCompressProcess:
    """ 适用于png图像的压缩 """
    COMPRESS_RATIO_ALLOWED = 0.95

    def __init__(self, **kwargs):
        # import uuid, tempfile
        # self.tmp_file = os.path.join(tempfile.gettempdir(), '{0}.quant.tmp.png'.format(uuid.uuid4().hex))
        self._setting = {
            "quant_file": 'pngquant',
            "min_quality": 65,
            "max_quality": 80,
            "speed": 3
        }
        self._setting.update(kwargs)
        self._pngquant_cmd = self.pngquant_cmd()

    def pngquant_cmd(self):
        s = self._setting
        cmd = "{} --quality={}-{} --speed={} --force -".format(s["quant_file"],
                                s["min_quality"], s["max_quality"], s["speed"])
        return cmd

    def _get_compression_ratio(self, origin_data, compressed_data):
        ratio = len(compressed_data) / len(origin_data)
        logger.debug(">>> PngQuant图像压缩比率: {}".format(ratio))
        return ratio

    def run(self, path_img):
        """ 如果转换导致质量低于最低质量，则不保存图像 """
        with open(path_img, "rb+") as fp:
            origin_data = last_data = fp.read()

            while True:
                # compressed_data = subprocess.check_output(cmd, shell=True)
                proc = subprocess.Popen(self._pngquant_cmd,
                                        shell=True,
                                        stdin=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        stdout=subprocess.PIPE)
                compressed_data, _err = proc.communicate(input=last_data)  # 阻塞
                if not compressed_data:
                    # if _err == '  error: Read error (libpng failed)\n  error: cannot decode image from stdin\n':
                    return compress_jpeg(path_img)

                compression_ratio = self._get_compression_ratio(last_data, compressed_data)
                if compression_ratio > self.COMPRESS_RATIO_ALLOWED:
                    if compression_ratio >= 1:
                        compressed_data = last_data
                    break
                else:
                    last_data = compressed_data

            total_ratio = self._get_compression_ratio(origin_data, compressed_data)
            if total_ratio < self.COMPRESS_RATIO_ALLOWED:
            # if last_data != origin_data:
                fp.seek(0)
                fp.truncate()
                fp.write(compressed_data)
        return total_ratio

from glob import glob

def listdir_img(dir_img, list_ext=None, recursive=True):
    if not list_ext:
        list_ext = ["png", "jpg", "jpeg"]
    list_ext.extend([ext.upper() for ext in list_ext])

    list_files = []
    for ext in list_ext:
        if recursive:
            list_files.extend(glob(r"{}/**/*.{}".format(dir_img, ext), recursive=True))
        else:
            list_files.extend(glob(r"{}/*.{}".format(dir_img, ext)))
    return list_files


_g_pngquant = ImageCompressProcess()
compress = _g_pngquant.run


if __name__ == "__main__":
    from utils.cli import Cli

    cli = Cli(description="Resize: 图像缩放与压缩工具")
    cli.getopt({
            "s,size": "缩放至尺寸，如: 800x600",
            "l,limit_size": "递归压缩至受限尺寸，如: 1280x800，可配合'-r'参数使用",
            "r,ratio": {
                # "default": 0.7,
                "type": float,
                "help": "缩放比例（默认: 0.7）"},
            "c,compress": {
                "action": "store_true",
                "help":"如果既没有设定ratio，也没有size，则执行压缩操作"},
            "p,path": "源文件路径",
            # "d,dst": "保存至文件夹",
        })

    # 处理其他参数
    def switch_args(cli, path_file):
        # print(">>>", path_file)
        args = cli.args
        if args.size:
            w, h = [int(n) for n in args.size.split("x")]
            resize(path_file, output_shape=[w,h])
        elif args.limit_size:
            w, h = [int(n) for n in args.limit_size.split("x")]
            ratio = args.ratio if args.ratio else 0.7
            resize(path_file, ratio=ratio, max_shape=[w,h])
        elif args.ratio:
            resize(path_file, ratio=args.ratio)
        # elif args.compress:
        else:
            # raise Exception("未知的指令")
            compress(path_file)

    # 处理路径参数（主要用于拖拽文件）
    if cli.args.path:
        cli.parse_path(cli.args.path, switch_args)
    else:
        inputs = input("\n请输入待处理文件path(支持直接拖拽): ")
        while True:
            list_path = cli.input_path_to_list(inputs)
            for path in list_path:
                cli.parse_path(path, switch_args)

            inputs = input("继续输入path，按[Q]退出: ")
            if inputs.lower() == "q":
                break
