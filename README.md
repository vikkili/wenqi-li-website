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
| `about.html` | 个人介绍 |
| `favicon.svg` | 站点图标 |

页面支持中英切换，语言偏好存在 `localStorage` 的 `site-lang` 里。

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

## 自定义域名

买好域名后：

```
./setup-domain.sh wenqili.net
```

脚本会同时绑定根域名和 `www`，并打印需要在注册商 DNS 面板添加的记录
（根域名走 TXT token 验证，`www` 走 CNAME 验证）。
DNS 生效后用 `./domain-status.sh` 查看验证与证书状态。

站点托管在香港（Azure 国际版），**不需要 ICP 备案** —— 备案只针对中国大陆境内的服务器。
