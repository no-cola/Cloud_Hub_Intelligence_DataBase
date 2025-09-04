<h2>云枢智库(CHID)</h2>
<h3>Cloud Hub Intelligence DataBase</h3>
<h3 align="right">——基于秘密共享的多方隐私保护数据库系统研究
</h3>


<h4>项目简介
本项目旨在研究和开发一种基于秘密共享的多方隐私保护数据库系统（MPC-DB），以解决在多方协作数据分析场景下，如何高效、安全地执行SQL查询语句的问题。通过结合安全多方计算（MPC）技术和数据库优化策略，本项目致力于构建一个功能完备、性能优越且隐私保护能力强大的数据库系统，推动隐私保护技术在商业智能、云计算等领域的应用落地。



#### 一、运行环境

- **操作系统**：Ubuntu 20.04/22.04 或 Windows WSL2 子系统

- **依赖内核**：Linux ≥ 5.10

- **网络**：可访问 GitHub 

  

#### 二、快速部署

##### 	1、获取源码

```bash
git clone https://github.com/no-cola/Cloud_Hub_Intelligence_DataBase.git
cd Cloud_Hub_Intelligence_DataBase
```

​		项目目录结构：

```markdown
Cloud_Hub_Intelligence_DataBase-main/
├── mpspdz/
```

##### 	2、一键初始化

​		运行setup.sh脚本进行基本的环境搭建

​		脚本将自动完成：

- Python3.10+、pip等构建

- MP-SPDZ 底层依赖与编译

  得到目录结构：

  ```markdown
  mpspdz/
  ├── replicated-ring-party.x          # 三方计算可执行程序
  ├── Programs/Source/
  │   ├── encode.mpc                   # 本地 CSV → 密文
  │   ├── decode.mpc                   # 密文 → 本地 CSV
  │   ├── select_query.mpc             # SQL 查询电路
  │   └── select_cache.mpc             # 缓存加速电路
  ├── cache/ db/ user/ user_information/ # 平台运行目录
  ```

##### 	3、启动平台

​		需要在app.py文件中修改数据库账户密码再在终端启动平台

​		加解密工具：

```
python3 user_app.py
```

​		安全多方计算平台：

```
python3 app.py
```

​		平台默认访问地址：https://localhost:65533



#### 三、项目功能

#### 本地数据加解密工具

**加密**：将CSV文件加密为多方计算格式

**解密**：将加密文件解密为原始的CSV格式

所有操作均在本地进行，不会泄露隐私数据，具有**安全**、**私密**的特点

加密得到的加密文件可直接在网页端进行下载，用于后续在安全多方计算平台上上传加密数据表



**`<!-- -->`**

#### 安全多方计算系统平台

基本功能有如下几种：上传加密数据表、SQL查询、数据表管理、流式SQL查询、查看流式任务以及添加邀请表



**上传加密数据表**

对于加解密工具中加密得到的加密文件可以在此上传并设置权限



**SQL查询**

对于已经上传且具有查询权限的数据表可以利用SQL查询语句执行查询，得到的结果可在网页端进行下载，后续可在加解密工具中进行解密得到CSV格式的数据表



**数据表管理**

显示上传的表名以及对应的列名等，行数通常不直接对受限访问者显示，管理员可在此获取到邀请码，其他用户可通过邀请码添加数据表



**流式SQL查询**

输入相应SQL查询语句并设置查询时间以及填写结果接收邮箱后即可开始流式查询，得到的查询结果会根据查询时间的设置发送到所填邮箱

这种实现可以让用户**不用登录数据库也能实时掌握数据动态**



**我的流式任务**

可在此界面查看保存的流式查询任务



**添加邀请表**

用户在此输入邀请码便可添加对应的数据表



**`<!-- -->`**

#### 功能矩阵

| 模块                | 子功能         | 关键特性                       |
| ------------------- | -------------- | ------------------------------ |
| **本地加解密工具**  | CSV ↔ 密文互转 | 离线运行、零上传               |
| **数据表管理**      | 上传/删除/授权 | 邀请码机制、列级权限、行数脱敏 |
| **交互式 SQL 查询** | 标准 ANSI SQL  | 查询结果可下载、可二次解密     |
| **流式 SQL 订阅**   | 定时/事件触发  | 分钟级调度、邮件推送、任务启停 |





```
@inproceedings{Cloud Hub Intelligence DataBase,
    author = {Xinyuan Zhu,Jiaqi Li,Hengrui Qu,Chengyi Xiong},
    title = {{Cloud Hub Intelligence DataBase}: A secret sharing-based multi-party privacy-preserving database system},
    url = {https://github.com/no-cola/Cloud_Hub_Intelligence_DataBase},
}
```