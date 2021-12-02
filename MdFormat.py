#!/usr/bin/env python3
# @Date    : 2021-12-02
# @Author  : Bright (brt2@qq.com)
# @Link    : https://gitee.com/brt2

# https://www.sublimetext.com/docs/api_reference.html

import sublime
import sublime_plugin

import os.path
from base64 import b64encode
from hashlib import md5
from datetime import datetime

from .fmt_md import MarkdownFormatter

class NotSavedFile(Exception): pass
class NotMarkdownFile(Exception): pass


def get_categories(path_md, key_dirname):
    assert os.path.isabs(path_md)
    # assert path_md.find(os.path.abspath(self.db_mgr.repo_dir)) == 0

    # 通过相对路径
    # path_dir = Path(os.path.dirname(path_md)).as_posix()
    # path_parts = Path(os.path.dirname(path_md)).parts  # tuple
    path_parts = os.path.dirname(path_md).split(os.sep)

    assert key_dirname in path_parts, "Error: {} not in {}".format(key_dirname, path_parts)
    index = path_parts.index(key_dirname)
    return list(path_parts[index +1:])

dir_blog = "programming"

class MdFormatCommand(sublime_plugin.TextCommand):

    fmt = MarkdownFormatter()

    def __init__(self, *args, **kwgs):
        super().__init__(*args, **kwgs)
        # print(">>> 初始化MdFormatCommand")
        # self.settings = sublime.load_settings('imgpaste2.sublime-settings')
        self.type2method = {
            "doc_format": self.doc_format,
            "img2base64": self.img2base64
        }

    def run(self, edit, type):
        self.type2method[type](edit)

    def _reload_doc(self):
        if self.view.is_dirty():
            if not sublime.ok_cancel_dialog("是否保存"):
                raise NotSavedFile()
            self.view.run_command('save')

        path_currfile = self.view.file_name()
        _, ext = os.path.splitext(path_currfile)
        if ext != ".md":
            # sublime.error_message("")
            # sublime.message_dialog("")
            if not sublime.ok_cancel_dialog("当前文档非.md文档，是否继续"):
                raise NotMarkdownFile()
        self.fmt.load_file(path_currfile)

    def doc_format(self, edit):
        self._reload_doc()

        # 传入文档路径的list，作为category
        self.fmt.metadata['categories'] = get_categories(self.fmt.file_path, dir_blog)

        self.fmt.format()
        self.fmt.overwrite()

    def img2base64(self, edit):
        self._reload_doc()
        dict_images = self.fmt.get_images("local")

        # self.fmt.process_images(dict_images, lambda xxx: pass)
        self.fmt.unlock_text()

        for line_idx, url_img in dict_images.items():
            url_new = (url_img)
            with open(url_img, "rb") as fp:
                img_buff = fp.read()
                img_base64 = b64encode(img_buff)  # bytes

                salt = str(datetime.now()).encode()
                md5obj = md5(salt)
                md5obj.update(img_buff)
                tmp_label = md5obj.hexdigest()

            num_space = self.fmt.get_text()[line_idx].find("!")
            self.fmt.modify_text(line_idx, " "*num_space + "![][%s]" % tmp_label)
            self.fmt.append_text("\n\n[%s]:data:image/png;base64,%s" % (tmp_label, img_base64.decode()))
        self.fmt.overwrite()
