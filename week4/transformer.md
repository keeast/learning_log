# 自注意力机制（self-attention）
## 问题情景
- 输入不是一个向量，而是多个向量，而且数量可能变化。  
例如文字处理、声音讯号、图  
- 输出：每一个输入向量都有一个对应的标签（Sequence Labeling）；  
    只需要输出一个标签；  
    模型自己决定输出多少个标签（**seq2seq**）
## Self-Attention原理
- 接受所有输入向量，输出相同数量的新向量，所以可以综合所有的信息  
![alt text](image.png)  
- self-attention内部：
![alt text](image-1.png)  
步骤：  
  - 计算任意两个向量之间的α（attention score），为了找出与a1相关的向量，计算方法如下：  
  ![alt text](image-2.png)
  - 对α激活得到α'  
  ![alt text](image-3.png)
  - 计算b1  
  ![alt text](image-4.png)  
  - 矩阵表示：
  ![alt text](image-5.png)
- 可以叠加很多次
## 改进版Multi-head Self-attention
用来处理不同种类的相关性  
![alt text](image-6.png)
## Positional Encoding位置编码
- 为了处理位置信息，为每一个位置设定一个向量e，将位置编码加到输入中
![alt text](image-7.png)
## 图片也可以引入self-attention
![alt text](image-8.png)  
## CNN和self-attention的关系  
CNN可以看作简化版的self-attention，因为CNN每次只考虑一个感受野内的信息，而self-attention考虑全图；self-attention在特定限制下可以和CNN相同
## RNN和self-attention的关系  
- self-attention可以平行处理所有输出，而RNN需要先后计算，运算效率更低
## self-attention用于图
- 图本身就包含了哪些节点之间是有关系的，所以可以无需计算部分节点之间的attention score，这就是一种类型的**GNN**