---
name: nat-hole-repo
version: 1.0.0
description: NAT Hole
trigger_conditions:
  - 需要理解、修改或排障 nat-hole 的代码
  - 在 nat-hole 里定位入口、数据表、对外契约或构建方式
---

# nat-hole 仓库技能

> 由仓库实际内容生成的骨架（README/目录/模型定义/契约/构建脚本逐项取证）。新增判断与坑位请直接在下面对应小节补充。

## 定位

**NAT Hole**

there is a server on internet, each p2p node heart beat with this server when node A want to connect to node B, it talk server its want to connect to node b, and it want b to connect to its port. then server reply A with node B's ip and port on internet, and forward A's info to node B A connnect to 

- 远端：`https://github.com/yumoqing/nat-hole.git`
- 默认分支：`master`（共 90 个提交）
- 最近提交：2021-05-11 `790ea81` bugfix
- 规模：23 个文件；Python 8，JSON 5，Shell 1

## 目录结构

- `conf/` — 配置（`config.json`；密码为 AES 密文）（7 个文件）
- `nathole/` — 6 个文件
- `nodeA/` — 2 个文件
- `nodeB/` — 2 个文件
- `nodeC/` — 2 个文件
- `test1/` — 2 个文件
- 根文件：`README.md`、`genrsa.sh`

## README 要点与注意（摘自 `README.md`）

- 章节：Outside server

## 建议阅读顺序

1. `README.md`

