# Wenqi Li — Personal Academic Website

Personal website of Wenqi Li, Assistant Professor in the Department of
Information Management at Peking University.

**Live site:** https://lemon-hill-09f2dea00.7.azurestaticapps.net

托管在 Azure Static Web Apps（East Asia / 香港，Free 层）。

## 结构

纯静态站点，没有构建步骤，CSS 和 JS 全部内联在各页面中。

| 文件 | 内容 |
|---|---|
| `index.html` | 首页 |
| `research.html` | 科研方向、项目与成果 |
| `teaching.html` | 教授课程 |
| `cv.html` | 简历（内嵌 `Wenqi_Li_CV.pdf`） |
| `about.html` | 个人介绍与相册 |
| `favicon.svg` | 站点图标 |
| `photo/web/` | 相册用图，**自动生成，不要手改** |

页面支持中英切换，语言偏好存在 `localStorage` 的 `site-lang` 里。

## 加照片

把新照片放进 `photo/`，按 `事件'年@地点N` 命名，例如：

    CHI'26@Barcelona3.HEIC
    ISIC'24@Denmark10.jpg

同一个 label 的照片会自动归成一组（叠放 + 点开轮播）。HEIC / JPG / PNG 都可以，
原图多大都行。加完之后让 Claude 重新生成一次，它会转成 JPEG、压到网页尺寸输出到
`photo/web/`，并更新 `about.html` 里的相册数据。

原图不入库（见 `.gitignore`），只保留在本地。

## 部署

托管在 Azure Static Web Apps，资源组 `wenqi-website-rg`，应用名 `wenqi-li-website`。

先登录（租户带 MFA，只需做一次，令牌会缓存）：

```
az login --tenant a82c9fc8-1578-43ec-9302-b3f3e83acf22
```

然后一条命令部署：

```
./deploy.sh
```

脚本会把该公开的文件挑到临时目录（原图不上传），取部署令牌，推送到 production 环境。

`staticwebapp.config.json` 控制缓存时长、安全响应头和 404 页面（`404.html`）。
Git 推送到 GitHub 只是版本管理，不会触发部署 —— 部署要跑 `./deploy.sh`。
