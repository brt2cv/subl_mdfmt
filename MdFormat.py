#!/usr/bin/env python3
# @Date    : 2021-12-23
# @Author  : Bright (brt2@qq.com)
# @Link    : https://gitee.com/brt2

# https://www.sublimetext.com/docs/api_reference.html

import sublime
import sublime_plugin

import os.path
import subprocess

from base64 import b64encode
from hashlib import md5
from datetime import datetime
from urllib.request import urlopen

from .formatter.md_fmt import MarkdownFormatter
from .cnblog.cnblog import CnblogManager, get_categories
from .cnblog.main import NoteRepoMgr

def subproc_run(command):
    # command = ['python3', os.path.join(dirname, 'bin/clipboard.py')]
    # str_cmd = " ".join(command)
    return subprocess.Popen(command,
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE)
                            # stderr=subprocess.STDOUT)

def md5sum(data, salt=None):
    if salt is None:
        salt = str(datetime.now()).encode()

    md5obj = md5(salt)
    md5obj.update(data)
    return md5obj.hexdigest()

class NotSavedFile(Exception): pass
class NotMarkdownFile(Exception): pass
class NotUpdateLatest(Exception): pass
class NoConfigFile(Exception): pass

class MdFormatCommand(sublime_plugin.TextCommand):

    fmt = MarkdownFormatter()

    def __init__(self, *args, **kwgs):
        super().__init__(*args, **kwgs)
        # print(">>> 初始化MdFormatCommand")
        self.settings = sublime.load_settings('settings.sublime-settings')
        self.type2method = {
            "doc_format": self.doc_format,
            "upload_prepare": self.upload_prepare,
            "upload": self.upload,
            "img2base64": self.img2base64
        }
        self.cnblog_init()

    def cnblog_init(self):
        path_curr = os.path.abspath(__file__)
        path_cnblog_account = os.path.join(os.path.dirname(path_curr), ".cnblog.json")
        if not os.path.exists(path_cnblog_account):
            sublime.error_message("【MdTools】插件未找到配置文件.cnblog.json")
            raise NoConfigFile()
        cnblog_mgr = CnblogManager(path_cnblog_account)
        self.note_mgr = NoteRepoMgr(cnblog_mgr)

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
        self.fmt.metadata['categories'] = get_categories(self.fmt.file_path,
                                          self.settings.get("blog_dir_name", ""))
        self.fmt.format()
        self.fmt.overwrite()

    def upload_prepare(self, edit):
        self.note_mgr.commit_repo()

    def upload(self, edit):
        if not sublime.ok_cancel_dialog("请确认当前仓库已经pull至最新版本"):
            raise NotUpdateLatest()
        self.note_mgr.push()

    def img2base64(self, edit):
        self._reload_doc()

        dict_images = self.fmt.get_images("local")
        # self.fmt.process_images(dict_images, lambda xxx: pass)
        self.fmt.unlock_text()
        for line_idx, path_img in dict_images.items():
            with open(path_img, "rb") as fp:
                img_buff = fp.read()
                img_base64 = b64encode(img_buff)  # bytes

            tmp_label = md5sum(img_buff[:70])
            num_space = self.fmt.get_text()[line_idx].find("!")
            indent = " "*num_space
            self.fmt.modify_text(line_idx, "{}[{}]:data:image/png;base64,{}\n{}![][{}]".format(
                    indent, tmp_label, img_base64.decode(), indent, tmp_label
                ))

        dict_images = self.fmt.get_images("http")
        self.fmt.unlock_text()
        for line_idx, url_img in dict_images.items():
            resp = urlopen(url_img)
            img_buff = resp.read()
            img_base64 = b64encode(img_buff)  # bytes

            tmp_label = md5sum(img_buff[:70])
            num_space = self.fmt.get_text()[line_idx].find("!")
            indent = " "*num_space
            self.fmt.modify_text(line_idx, "{}[{}]:data:image/png;base64,{}\n{}![][{}]".format(
                    indent, tmp_label, img_base64.decode(), indent, tmp_label
                ))

        self.fmt.overwrite()
