# Linux命令行
## 什么是shell
- 复制粘贴：鼠标左键选中，右键可进行复制、粘贴  
- 聚焦方式：单击聚焦
- 查看磁盘剩余：`df`
- 显示空闲内存：`free`
- 结束终端会话：`exit`
## 文件系统中跳转
- 类Unix系统：只有单一的文件系统树
- 打印出当前工作目录名：`pwd`
- 更改目录：`cd`
- 列出目录内容：`ls`
- 文件路径：
  - 绝对路径：/usr/bin，根目录/下的usr目录下的bin目录
  - 相对路径：`.`当前目录、`..`当前目录的父目录
## 研究操作系统
- 选项和参数：
  ```bash
  command -options arguments
  ```
  选项：'-'+字符   
  长选项：'--'+字符
  ```bash
  ## -l：以长格式显示，--reverse：以相反的顺序来显示结果
  ls -lt --reverse
- 确定文件类型：`file filename`
- 浏览文件内容：`less filename`
## 操作文件和目录
- 复制文件和目录  
  ```bash
    # 将item1复制到item2
    cp item1 item2
  ```
- 通配符：
![alt text](image.png)  
- 创建目录：`mkdir dirl`
- 移动和重命名文件
  ```bash
    # 把文件或目录 “item1” 移动或重命名为 “item2”
    mv item1 item2
    ```
- 删除文件和目录`rm`
- 链接：文件的有一个名字
  - 硬链接：不能跨越物理设备；不能关联目录  
    创建硬链接：`ln file link`
  - 符号链接：符号链接是文件的特殊类型，它包含一个指向目标文件或目录的文本指针  
    创建符号链接：`ln -s item link`
## 使用命令
- 四种命令：
  - 可执行程序：可编译成二进制文件，如python
  - 内建于shell自身的命令，如`cd`
  - shell函数，小规模shell脚本，混合到环境变量中
  - 命令别名，在其他命令上自定义
- 显示命令类型：`type`
- 显示可执行程序的位置：which
  ```bash
    which ls
- `help`：
  ```bash
    ## 得到**shell内部命令**的帮助文档
    help cd
    ## 显示可执行程序用法信息
    mkdir --help
- `man`:显示程序手册页
- `apropos`：搜索关键字
- `whatis`：  