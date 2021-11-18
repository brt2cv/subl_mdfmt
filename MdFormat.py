#!/usr/bin/env python3
# @Date    : 2021-11-18
# @Author  : Bright (brt2@qq.com)
# @Link    : https://gitee.com/brt2

import sublime
import sublime_plugin

from .fmt_md import MarkdownFormatter

class MdFormatCommand(sublime_plugin.TextCommand):
    def __init__(self, *args, **kwgs):
        super().__init__(*args, **kwgs)
        print(">>> 初始化MdFormatCommand")
        # self.settings = sublime.load_settings('imgpaste2.sublime-settings')

    def run(self, edit):
        """ """
        path_currfile = self.view.file_name()
        # print(">>>", path_currfile)
        fmt = MarkdownFormatter()
        fmt.load_file(path_currfile)
        fmt.format()
        fmt.overwrite()
