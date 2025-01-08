# 配置

> 敏感数据直接配置在pycharm的variable enviroment中

1. chatgpt：在model.py中设置api_key

   * 基本付费价格：一百万输入token需要3美元，一百万输出token需要6美元

   * 会员：修改月使用额度，分钟使用额度

     <img src="https://arnovc.oss-cn-beijing.aliyuncs.com/img/image-20250107155605800.png" alt="image-20250107155605800" style="zoom:50%;" />

     <img src="https://arnovc.oss-cn-beijing.aliyuncs.com/img/image-20250107155636575.png" alt="image-20250107155636575" style="zoom:50%;" />

2. bing：

   * 在model.py中设置api_key
   * 在run.py中设置end_point

   注：调用v7的api需要较高的**定价层**(至少S16是可以的)



# 数据指标

> 测试使用的LLM：gpt-3.5-turbo

1. 数据集

   * scienceQA
     * 类型：多模态
     * 问题个数：21208
     * 输入类型：文字+图片
     * 输出类型：字母
   * tabmwp
     * 类型：表格+计算题
     * 问题个数：38431
     * 输入类型：文字+表格
     * 输出类型：数值

   注：我这边能不能统一一下，通过一些标志位提前告诉chatgpt当前的输入有表格或文字等

2. 源代码测试

   | 数据集    | 总数 | 正确个数 | 正确率 |
   | --------- | ---- | -------- | ------ |
   | scienceQA | 424  | 275      | 65%    |
   | tabmwp    | 424  | 212      | 50%    |

   注：
   
   * 具体题目编号
     * scienceQA数据集：[16810,12979,11202,18743,21025,13738,2660,6967,12995,19819]
     * tabmwp数据集：
   * 测试200问题的scienceQA消费\$0.48，\$tabmwp消费1.15
   
3. cmp分支

   



# 常见错误

1. ssl错误：需要关闭VPN
1. 需要连接实验室的网络才能正常运行
1. Rate limit reached for gpt-3.5-turbo in organization org-BBnzYaTwJ8tcEakrZt6q67tz on tokens per min (TPM): Limit 200000, Used 197337, Requested 4000. Please try again in 401ms：分钟内请求过多，需要加钱升级用户权限



------

1. 构建工具的基本方式比较
   * cot：[solution generator,answer generator]
   * pot：[program generator, program executor, answer generator]
   * chamelon
2. 由于scienceQA与tabmwp的输入和输出格式完全不同，故两个benchmark的处理方式基本不同
3. pot仅仅在tabmwp中有应用到
4. 跑程序存在的问题：chatgpt接口的开销较大
5. scienceqa数据集增加tabmwp模块存在的问题：program generator, column lookup等
   * 两个benchmark数据结构不一致，相关代码无法直接从一个benchmark移植到另一个benchmark
   * 和program相关的样例都是基于tabmwp，scienceqa对新模块的调用率极低
6. 两步策略
   * 增加模块，同时观察调用率
   * 提高准确度
7. git的三种提交
   * 配置：文档及参数等
   * 功能：功能模块
   * 修复：修复bug
8. 关于chatgpt中的model和engine：旧版使用engine，新版使用Model，感觉混用的问题不大
