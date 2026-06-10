# 成功日记 PWA - 部署指南

## 方案一：Railway（推荐，最省心）

1. **注册/登录** https://railway.com （用 GitHub 登录）
2. **创建项目** → 选择 "Deploy from GitHub repo"
3. **连接仓库** → 选 `success-diary` 仓库
4. **Root Directory** → 留空（从项目根目录部署）
5. **Start Command** → 自动从 railway.json 读取
6. **部署完成** → Railway 会自动生成 `*.railway.app` 链接

## 方案二：Render

1. **注册** https://render.com （用 GitHub 登录）
2. **New Web Service** → 连接仓库
3. **Root Directory** → `backend`
4. **Build Command** → `pip install -r requirements.txt`
5. **Start Command** → `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2`
6. **部署完成**

## 方案三：Fly.io

```bash
fly launch
fly deploy
```

## 使用方式

部署完成后，所有人都可以通过链接访问 PWA：
- 在 Safari/Chrome 中打开 → 点击"分享"→"添加到主屏幕"
- 就可以像原生 App 一样使用了