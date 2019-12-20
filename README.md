![](https://data-analysis.cn-shanghai.log.aliyuncs.com/logstores/article-logs/track_ua.gif?APIVersion=0.6.0&title=%E5%BF%AB%E9%80%9F%E6%90%AD%E5%BB%BAServerless%E4%BA%BA%E8%84%B8%E8%AF%86%E5%88%AB%E7%A6%BB%E7%BA%BF%E6%9C%8D%E5%8A%A1&author=zechen&src=article)

# 快速搭建 Serverless 人脸识别离线服务

## 简介
首先介绍下在本文出现的几个比较重要的概念：
> 函数计算（Function Compute）：函数计算是一个事件驱动的服务，通过函数计算，用户无需管理服务器等运行情况，只需编写代码并上传。函数计算准备计算资源，并以弹性伸缩的方式运行用户代码，而用户只需根据实际代码运行所消耗的资源进行付费。函数计算更多信息[参考](https://statistics.functioncompute.com/?title=%E5%BF%AB%E9%80%9F%E6%90%AD%E5%BB%BAServerless%E4%BA%BA%E8%84%B8%E8%AF%86%E5%88%AB%E7%A6%BB%E7%BA%BF%E6%9C%8D%E5%8A%A1&src=article&author=zechen&url=https://fc.console.aliyun.com/)
> 函数工作流（Function Flow）：函数工作流是一个用来协调多个分布式任务执行的全托管云服务。用户可以用顺序，分支，并行等方式来编排分布式任务，FnF 会按照设定好的步骤可靠地协调任务执行，跟踪每个任务的状态转换，并在必要时执行用户定义的重试逻辑，以确保工作流顺利完成。函数工作流更多信息[参考](https://statistics.functioncompute.com/?title=%E5%BF%AB%E9%80%9F%E6%90%AD%E5%BB%BAServerless%E4%BA%BA%E8%84%B8%E8%AF%86%E5%88%AB%E7%A6%BB%E7%BA%BF%E6%9C%8D%E5%8A%A1&src=article&author=zechen&url=https://fnf.console.aliyun.com/)

本文将重点介绍如何快速地通过函数计算与函数工作流部署一个定时离线批量处理图片文件并标注出人脸的服务。

__开通服务__
1. [免费开通函数计算](https://statistics.functioncompute.com/?title=%E5%BF%AB%E9%80%9F%E6%90%AD%E5%BB%BAServerless%E4%BA%BA%E8%84%B8%E8%AF%86%E5%88%AB%E7%A6%BB%E7%BA%BF%E6%9C%8D%E5%8A%A1&src=article&author=zechen&url=https://fc.console.aliyun.com/)，按量付费，函数计算有很大的免费额度。
2. [免费开通函数工作流](https://statistics.functioncompute.com/?title=%E5%BF%AB%E9%80%9F%E6%90%AD%E5%BB%BAServerless%E4%BA%BA%E8%84%B8%E8%AF%86%E5%88%AB%E7%A6%BB%E7%BA%BF%E6%9C%8D%E5%8A%A1&src=article&author=zechen&url=https://fnf.console.aliyun.com/)，按量付费，目前该产品在公测阶段，可以免费使用。
3. [免费开通对象存储](https://statistics.functioncompute.com/?title=%E5%BF%AB%E9%80%9F%E6%90%AD%E5%BB%BAServerless%E4%BA%BA%E8%84%B8%E8%AF%86%E5%88%AB%E7%A6%BB%E7%BA%BF%E6%9C%8D%E5%8A%A1&src=article&author=zechen&url=https://oss.console.aliyun.com/)，按量付费。

__解决方案__


[![](https://img.alicdn.com/tfs/TB1upSqrkT2gK0jSZFkXXcIQFXa-827-477.png)](https://statistics.functioncompute.com/?title=%E5%BF%AB%E9%80%9F%E6%90%AD%E5%BB%BAServerless%E4%BA%BA%E8%84%B8%E8%AF%86%E5%88%AB%E7%A6%BB%E7%BA%BF%E6%9C%8D%E5%8A%A1&src=article&author=zechen&url=https://fc.console.aliyun.com/)

流程如下：
1. 设定定时触发器，定时触发函数计算中的函数。
2. 函数被触发后，调用一次函数工作流中的流程。
3. 函数工作流中的流程被执行:
   1. 调用函数计算中的函数，列举出 OSS Bucket 根路径下的图片文件列表。
   2. 对于步骤1中列出的文件列表，对每个文件：
      - 调用函数计算中的函数处理，进行人脸识别并标注。将标注后的文件存入 OSS，最后将处理过的文件进行转移。
   3. 判断当前 OSS 根路径下是否有更多的文件
      - 如是，继续步骤1
      - 如否，结束流程

## 快速开始
1. Clone 工程到本地
   - `git clone git@github.com:ChanDaoH/serverless-face-recognition.git`
2. 替换项目目录下 template.yml 文件中的 `YOUR_BUCKET_NAME` 为在杭州区域的 OSS Bucket (可以不是杭州区域的，需要同步修改 `OSS_ENDPOINT`)
  ```
  ROSTemplateFormatVersion: '2015-09-01'
  Transform: 'Aliyun::Serverless-2018-04-03'
  Resources:
    face-recognition:
      Type: 'Aliyun::Serverless::Service'
      Properties:
        Policies:
          - Version: '1'
            Statement:
              - Effect: Allow
                Action:
                  - 'oss:ListObjects'
                  - 'oss:GetObject'
                  - 'oss:PutObject'
                  - 'oss:DeleteObject'
                  - 'fnf:*'
                Resource: '*'
      listObjects:
        Type: 'Aliyun::Serverless::Function'
        Properties:
          Handler: index.handler
          Runtime: python3
          Timeout: 60
          MemorySize: 128
          CodeUri: functions/listobjects
          EnvironmentVariables:
            OSS_ENDPOINT: 'https://oss-cn-hangzhou-internal.aliyuncs.com'
      detectFaces:
        Type: 'Aliyun::Serverless::Function'
        Properties:
          Handler: index.handler
          Runtime: python3
          Timeout: 60
          MemorySize: 512
          CodeUri: functions/detectfaces
          EnvironmentVariables:
            OSS_ENDPOINT: 'https://oss-cn-hangzhou-internal.aliyuncs.com'
      timer:
        Type: 'Aliyun::Serverless::Function'
        Properties:
          Handler: index.handler
          Runtime: python3
          Timeout: 60
          MemorySize: 512
          CodeUri: functions/timer
        Events:
          timeTrigger:
            Type: Timer
            Properties:
              CronExpression: '0 * * * * *'
              Enable: true 
              # replace YOUR_BUCKET_NAME to your oss bucket name
              Payload: '{"flowName": "oss-batch-process", "input": "{\"bucket\": \"YOUR_BUCKET_NAME\",\"prefix\":\"\"}"}'
    oss-batch-process:
      Type: 'Aliyun::Serverless::Flow'
      Properties:
        Description: batch process flow
        DefinitionUri: flows/index.flow.yml
        Policies:
          - AliyunFCInvocationAccess
  ```
3. 一键部署函数计算和函数工作流资源至云端
   - 安装最新版本的 [Fun](https://github.com/alibaba/funcraft)
   - 在项目根目录下执行 `fun deploy`

## 效果验证
1. 在 OSS Bucket 的根目录下放置图片

[![](https://img.alicdn.com/tfs/TB1S4GsrbY1gK0jSZTEXXXDQVXa-2332-714.png)](https://statistics.functioncompute.com/?title=%E5%BF%AB%E9%80%9F%E6%90%AD%E5%BB%BAServerless%E4%BA%BA%E8%84%B8%E8%AF%86%E5%88%AB%E7%A6%BB%E7%BA%BF%E6%9C%8D%E5%8A%A1&src=article&author=zechen&url=https://fc.console.aliyun.com/)

2. 等待一分钟后，定时触发器触发函数执行函数工作流。

[![](https://img.alicdn.com/tfs/TB1gJesrhv1gK0jSZFFXXb0sXXa-2344-1216.png)](https://statistics.functioncompute.com/?title=%E5%BF%AB%E9%80%9F%E6%90%AD%E5%BB%BAServerless%E4%BA%BA%E8%84%B8%E8%AF%86%E5%88%AB%E7%A6%BB%E7%BA%BF%E6%9C%8D%E5%8A%A1&src=article&author=zechen&url=https://fc.console.aliyun.com/)

3. 工作流执行完成后，查看 OSS Bucket
   - 标注出人脸的图像放置在 `face-detection` 目录下

[![](https://img.alicdn.com/tfs/TB1yLDUqubviK0jSZFNXXaApXXa-2768-1580.png)](https://statistics.functioncompute.com/?title=%E5%BF%AB%E9%80%9F%E6%90%AD%E5%BB%BAServerless%E4%BA%BA%E8%84%B8%E8%AF%86%E5%88%AB%E7%A6%BB%E7%BA%BF%E6%9C%8D%E5%8A%A1&src=article&author=zechen&url=https://fc.console.aliyun.com/)

   - 处理过的录像放置在 `processed` 目录下

[![](https://img.alicdn.com/tfs/TB1BPSprkL0gK0jSZFtXXXQCXXa-1378-818.gif)](https://statistics.functioncompute.com/?title=%E5%BF%AB%E9%80%9F%E6%90%AD%E5%BB%BAServerless%E4%BA%BA%E8%84%B8%E8%AF%86%E5%88%AB%E7%A6%BB%E7%BA%BF%E6%9C%8D%E5%8A%A1&src=article&author=zechen&url=https://fc.console.aliyun.com/)


## 总结
通过 [函数计算](https://statistics.functioncompute.com/?title=%E5%BF%AB%E9%80%9F%E6%90%AD%E5%BB%BAServerless%E4%BA%BA%E8%84%B8%E8%AF%86%E5%88%AB%E7%A6%BB%E7%BA%BF%E6%9C%8D%E5%8A%A1&src=article&author=zechen&url=https://fc.console.aliyun.com/) + [函数工作流](https://statistics.functioncompute.com/?title=%E5%BF%AB%E9%80%9F%E6%90%AD%E5%BB%BAServerless%E4%BA%BA%E8%84%B8%E8%AF%86%E5%88%AB%E7%A6%BB%E7%BA%BF%E6%9C%8D%E5%8A%A1&src=article&author=zechen&url=https://fnf.console.aliyun.com/)，搭建了一个定时批量处理图片进行人脸识别的服务。该服务因为使用了函数工作流的流程，将任务分为了多个步骤，只需要确保每个步骤的函数能够在函数计算限制时间(10分钟)内完成即可。
通过 [Fun](https://github.com/alibaba/funcraft) 工具，一键部署 [函数计算](https://statistics.functioncompute.com/?title=%E5%BF%AB%E9%80%9F%E6%90%AD%E5%BB%BAServerless%E4%BA%BA%E8%84%B8%E8%AF%86%E5%88%AB%E7%A6%BB%E7%BA%BF%E6%9C%8D%E5%8A%A1&src=article&author=zechen&url=https://fc.console.aliyun.com/) + [函数工作流](https://statistics.functioncompute.com/?title=%E5%BF%AB%E9%80%9F%E6%90%AD%E5%BB%BAServerless%E4%BA%BA%E8%84%B8%E8%AF%86%E5%88%AB%E7%A6%BB%E7%BA%BF%E6%9C%8D%E5%8A%A1&src=article&author=zechen&url=https://fnf.console.aliyun.com/)，免去去多平台进行操作的步骤。

__相关参考__
1. [函数计算](https://statistics.functioncompute.com/?title=%E5%BF%AB%E9%80%9F%E6%90%AD%E5%BB%BAServerless%E4%BA%BA%E8%84%B8%E8%AF%86%E5%88%AB%E7%A6%BB%E7%BA%BF%E6%9C%8D%E5%8A%A1&src=article&author=zechen&url=https://fc.console.aliyun.com/)
2. [函数工作流](https://statistics.functioncompute.com/?title=%E5%BF%AB%E9%80%9F%E6%90%AD%E5%BB%BAServerless%E4%BA%BA%E8%84%B8%E8%AF%86%E5%88%AB%E7%A6%BB%E7%BA%BF%E6%9C%8D%E5%8A%A1&src=article&author=zechen&url=https://fnf.console.aliyun.com/)
3. [Aliyun Serverless VSCode 插件](https://github.com/alibaba/serverless-vscode/)
4. [Fun](https://github.com/alibaba/funcraft)

__参考示例__
1. [serverless-face-recognition](https://github.com/ChanDaoH/serverless-face-recognition)
2. [oss-batch-process](https://github.com/awesome-fnf/oss-batch-process)