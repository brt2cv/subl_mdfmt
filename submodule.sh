#!/bin/bash
# submodule is link, subtree is copy

test -z $1 && action="pull" || action=$1  # echo "Error: 请显式定义操作!" && exit

function clone_or_pull () {
dir_name=$1
url_repo=$2
branch=$3
others=${*:4}

    if [ -d $dir_name ]; then
        cd $dir_name
        echo "尝试更新 ${dir_name} 模块"
        # git checkout $branch
        git pull
        cd - > /dev/null
    else
        echo "克隆仓库 ${url_repo} --> ${dir_name}"
        git clone $url_repo $dir_name $others
        cd $dir_name
        if [ $? -eq 0 ]; then
            git checkout $branch
            test $? -eq 0 && echo "已切换至${branch}分支" || echo "无法切换分支${branch}"
            cd - > /dev/null
        fi
    fi
}

function subtree_pull () {
dir_module=$1
url_repo=$2
branch=$3

    if [ -d $dir_module ]; then
        git subtree pull --prefix=$dir_module $url_repo $branch --squash
    else
        read -p "是否载入子模块 [y/N]" continue
        if [ ${continue}_ == "y_" ]; then
            git subtree add --prefix=$dir_module $url_repo $branch --squash
        fi
    fi
}

function subtree_push () {
dir_module=$1
url_repo=$2
branch=$3

    git subtree push --prefix=$dir_module $url_repo $branch
}

function submodule_pull () {
dir_module=$1
url_repo=$2
branch=$3

    if [ -d $dir_module ]; then
        cd $dir_module && git checkout $branch && git pull && cd ..
        # git submodule foreach git pull
            echo ">> 子模块已更新，请在主仓库commit子模块引用信息"
    else
        read -p "是否载入子模块 [y/N]" continue
        if [ ${continue}_ == "y_" ]; then
            # git subtree add --prefix=$dir_module $url_repo $branch --squash
            git submodule add $url_repo $dir_module
            echo ">> 请手动切换子模块分支: " $dir_module
            cd $dir_module && git checkout $branch && cd ..
            echo ">> 然后在主仓库commit子模块引用信息"
        fi
    fi
}

function submodule_push () {
dir_module=$1
url_repo=$2
branch=$3

    echo ">> 请确保在主仓库更新前，先提交子模块。然后手动push子模块仓库即可"
    # read -p ">> 输入commit信息: " message
    # cd $dir_module && git add *
    # git commit -m $message && cd ..
}

#####################################################################

# m_etc="git@gitee.com:brt2/etc.git"
# m_pystr="https://github.com/brt2cv/pystring.git"
m_cnblog="https://github.com/brt2cv/note2cnblog.git"

if [ $action == "push" ]; then
    # 子模块
    # subtree_push data $m_cnblog master

    # submodule
    submodule_push cnblog $m_cnblog master

    # 子项目
    # echo "如需推送，请直接到子仓库中执行 `git push`"
    exit
elif [ $action == "pull" ]; then
    # 子模块
    # subtree_pull data $m_cnblog master

    # submodule
    submodule_pull cnblog $m_cnblog master

    # 子项目
    # clone_or_pull etc $m_etc master
    exit
else
    echo "未知的指令参数: ${action}"
    exit
fi
