# 叶片病害图片来源（无需 key，可直接下）

> Demo 只需 2–3 张就够。**走 PlantVillage 数据集（CC0 / CC-BY-SA 3.0）**，
> 不要随便从百度图片抓，版权和分辨率都不可控。

## PlantVillage 下载入口

- 官方页：https://plantvillage.psu.edu/posts/6948-plantvillage-dataset-download
- Kaggle 镜像（最快下，免登录）：https://www.kaggle.com/datasets/emmarex/plantdisease
- GitHub（原始 spMohanty）：https://github.com/spMohanty/PlantVillage-Dataset
- Mendeley：https://data.mendeley.com/datasets/tywbtsjrjv/1

## 我们 demo 用得上的类别（玉米相关）

| 文件夹 | 含义 | 适合 demo 哪个剧本 |
| --- | --- | --- |
| `Corn_(maize)___Common_rust_` | 玉米普通锈病 | 黄淮春末夏初锈病爆发 |
| `Corn_(maize)___Northern_Leaf_Blight` | 大斑病 | 东北/华北玉米中后期叶斑 |
| `Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot` | 灰斑病 | 西南/黄淮高湿地块 |
| `Corn_(maize)___healthy` | 健康对照 | "vs 健康"对比页 |

## 缺什么

- PlantVillage 里**没有小麦**（条锈病/赤霉病）。
- 小麦病叶想要真实图：
  - **CGIAR Wheat Rust Photo Library**（CC-BY）：https://wheatrust.org/photo-gallery（部分需注明 CIMMYT）
  - 或者中国植保学会公众号文章配图，要逐张确认授权
- demo 凑合方案：小麦病害的图先**用占位图 + 文字描述**，玉米病害走 PlantVillage 真图。

## 落地建议

```
backend/static/demo_leaves/
├── corn_common_rust_01.jpg          # PlantVillage
├── corn_common_rust_02.jpg          # PlantVillage
├── corn_nlb_01.jpg                  # PlantVillage
├── corn_healthy_01.jpg              # PlantVillage
└── wheat_stripe_rust_placeholder.jpg  # 占位
```

田间影像 Collector 只要把上面这几张 URL 当成 `/api/parcels/<id>/photos` 的返回即可。
