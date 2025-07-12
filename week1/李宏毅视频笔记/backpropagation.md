# BackPropagation（反向传播）
- 原理：链式法则  
![alt text](image2/image-4.png)
- 正向传播和反向传播  
![alt text](image2/image-5.png)
  - Forward Pass  
为什么z对w的微分叫正向传播：  
因为只要一直往前计算，知道i-1层的输出，就可以知道第i层中z对w的微分，如下图  
![alt text](image2/image-6.png)  
  - Backward pass  
  ![alt text](image2/image-7.png)  
  由上图及链式法则可得：![alt text](image2/image-9.png)  
  因为sigmoid函数及其微分如下：  
  ![alt text](image2/image-10.png)  
  所以可算得：![alt text](image2/image-11.png)  
  由链式法则得：![alt text](image2/image2/image-13.png)  
  在正向传播时z已经确定，所以对z的微分是一个常数  
  ![alt text](image2/image-14.png)  
  为什么叫反向传播：知道后一个可递归得前一个的微分
- 总结：反向传播相当于构建一个方向相反的神经网络，计算就相当于正向传播  
![alt text](image2/image-15.png)