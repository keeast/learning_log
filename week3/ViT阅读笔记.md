# AN IMAGE IS WORTH 16X16 WORDS:    TRANSFORMERS FOR IMAGE RECOGNITION AT SCALE
- 论文链接：https://arxiv.org/pdf/2010.11929.pdf
- 作者：Alexey Dosovitskiy, Lucas Beyer, Alexander Kolesnikov 等11位Google Brain团队成员
- 核心贡献：**首次证明纯Transformer架构（无需CNN）可以直接应用于图像分类任务，并在大规模数据上达到SOTA水平**
## 2. 核心创新点
### 2.1 背景    
在ViT提出之前，Transformer在NLP领域已成为主流，但在CV中的应用仍非常有限。此前虽有将Self-Attention与CNN结合的工作，但纯Transformer结构的视觉模型尚未出现。

将Transformer直接用于图像的主要障碍是序列长度问题：一张224×224的图像有50176个像素，若每个像素作为一个token，自注意力的O(n²)复杂度将导致计算开销巨大

### 2.2 核心思路
**把图像切分成固定大小的图像块（Patch），将每个Patch当作NLP中的一个“词”（Word）** 。论文标题"An Image is Worth 16x16 Words"正是对这一思想的高度概括——一张图像被表示为若干个16×16像素的图像块序列。

- 将输入图像（如224×224）划分为N个不重叠的Patch，每个Patch大小为P×P（论文默认P=16）

- N = (H/P) × (W/P)，例如224/16=14，则N=14×14=196个Patch

- 这196个Patch组成一个序列，作为Transformer Encoder的输入

### 2.3 原因分析
CNN天然具备**归纳偏置（Inductive Bias） ——局部性（locality）和平移不变性**（translation equivariance）。而Transformer没有这些先验知识，需要从数据中自己学习。

论文的关键发现是：当在**足够大的数据集**（如JFT-300M，约3亿张图像）上预训练时，大规模数据可以弥补Transformer缺乏归纳偏置的不足。在大规模预训练后，ViT在ImageNet上达到88.55%的准确率，与最先进的CNN相媲美甚至超越

## 3. Patch Embedding的原理（Conv2d实现图像块映射）
### 3.1 什么是Patch Embedding
- Patch Embedding是将原始图像块转换为模型可处理的向量表示的过程。每个Patch被展平（Flatten）后，通过一个线性投影层映射到固定维度的嵌入空间
    ```
    z₀ = [x_class; x_p¹E; x_p²E; ...; x_pᴺE] +   E_pos
    其中x_p是展平后的Patch，E是线性投影矩阵
    ```
- 为什么用Conv2d
    - 切分图像：卷积核大小=步长=Patch Size，意味着每个卷积窗口恰好覆盖一个不重叠的Patch区域

    - 线性映射：每个卷积核将P×P×3的Patch像素值，通过卷积运算加权求和，输出一个标量；多个卷积核（数量=embed_dim）则输出一个embed_dim维的向量
## 4. Class Token和Position Embedding
### 4.1 Class Token（分类标记）
- Class Token是一个可学习的特殊向量，被拼接在Patch Embedding序列的最前面。它借鉴了BERT模型中的[CLS]标记设计
- 作用：    
    - 聚合全局信息：在Transformer的多头自注意力机制中，Class Token可以与所有Patch Token进行信息交互。经过多层编码后，Class Token整合了整张图像的全局信息

    - 作为图像表征：最终取Transformer编码器输出的、对应Class Token位置的特征向量，作为整张图像的表示（Image Representation）

    - 输入分类头：这个表征向量被送入MLP分类头，输出最终的分类结果
### 4.2 Position Embedding（位置编码）
- 为什么需要：CNN通过卷积操作天然保留了空间位置关系，而Transformer需要显式地注入位置信息
- 位置编码方式：可学习的1D位置编码
    - 为序列中的每个位置（包括Class Token的位置和所有Patch的位置）分配一个可学习的向量

    - 这些位置向量与对应的Token向量相加（而非拼接）

    - 位置编码在训练过程中与其他参数一起优化更新


## 5. ViT vs. CNN 对比表

| **对比维度** | **Vision Transformer (ViT)** | **卷积神经网络 (CNN)** |
| :--- | :--- | :--- |
| **核心机制** | 多头自注意力（Multi-head Self-Attention），建模全局依赖关系 | 卷积核滑动提取局部特征，通过堆叠层扩大感受野 |
| **图像处理方式** | 将图像切分为固定大小的 **Patch（图像块）**，视为序列输入 | 直接在像素网格上滑动卷积核，处理局部邻域 |
| **归纳偏置** | **较弱** – 不具备天然的空间局部性/平移等变性，需从数据中学习 | **较强** – 天然具备局部性（locality）和平移等变性（translation equivariance） |
| **数据效率** | **依赖大规模数据**（如 JFT-300M），中小数据集上性能可能不及 CNN | 在 **中小型数据集**（如 ImageNet-1K）上表现稳健，数据利用率高 |
| **计算复杂度** | 自注意力复杂度 O(N²)（N 为 Patch 数量），**计算成本高**；推理/训练显存开销大 | 卷积计算高效，复杂度与图像尺寸线性相关，**资源消耗相对较低** |
| **全局上下文建模** | **天生擅长** – 从第一层起即可捕获任意远距离像素/块之间的关系 | **能力有限** – 需深层堆叠或空洞卷积等特殊设计才能扩大感受野 |
| **空间位置建模** | 通过 **可学习位置编码（Position Embedding）** 显式注入位置信息 | 通过卷积操作的 **空间相对位置** 天然保留位置信息 |
| **可扩展性** | **强** – 随模型参数量和数据量增大，性能提升潜力巨大 | 扩展性受限于局部感受野，大规模模型收益递减 |
| **鲁棒性** | 对对抗扰动、遮挡、旋转等变换的 **鲁棒性相对较弱** | 因具备平移等变性，对常见图像变换的鲁棒性更好 |
| **可解释性** | 注意力权重可直观展示关注区域，但整体机制较难解释 | 卷积核可视化相对直接，但深层特征语义模糊 |
| **代表应用** | 大规模图像分类、多模态模型（如 CLIP）、需要全局理解的场景 | 目标检测、图像分割、人脸识别、嵌入式视觉任务 |
| **主要变体** | DeiT（数据高效）、Swin Transformer（层次化）、Hybrid ViT（融合 CNN） | ResNet、EfficientNet、MobileNet、DenseNet |
| **预训练要求** | 通常需要在大规模数据集（如 ImageNet-21k 或 JFT）上预训练 | 可在 ImageNet-1K 上直接从头训练，效果良好 |
| **范式地位** | 代表 CV 领域从 **卷积范式** 向 **Transformer 范式** 的转移 | 传统视觉任务的 **主力基线（strong baseline）** |

---