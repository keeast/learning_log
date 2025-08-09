# conda命令
```bash
    # 创建虚拟环境
    conda create -n name python=3.9
    # 激活环境
    conda activate name
    # 退出当前环境
    conda deactivate
    # 列出所有环境
    conda env list
    # 删除所有环境
    conda remove --name myenv --all
    # 克隆环境
    conda create --clone myenv --name newenv
    # 导出环境到yaml文件
    conda env export > environment.yaml
    # 从yaml文件创建环境
    conda env create -f environment.yaml


    # 查看已安装的包
    conda list
    # 安装包
    conda install numpy pandas
    # 卸载包
    conda remove numpy

    # 显示所有配置
    conda config --show
    # 启动jupyter
    jupyter notebook