# Transformer
- seq2seq模型，可以处理如语音识别、机器翻译。transformer是一种seq2seq模型
- QA问题可以用seq2seq解决
- seq2seq的一般流程：  
![alt text](images/image-9.png)
- transformer中的encoder：  
![alt text](images/image-11.png)
![alt text](images/image-12.png)
- transformer中的decoder：
  - Autoregressive：
  ![alt text](images/image-14.png)  
  如何判断结束：输出一个END编码  
  ![alt text](images/image-15.png)
  - Non-autoregressive  
  一次性输出，并行化
  ![alt text](images/image-16.png)  
  怎么确定输出的长度：专门另外设一个预测器；或给尽可能多的begin，看哪里会输出end
- encoder和decoder之间的连接  
**cross attention**  
![alt text](images/image-17.png)