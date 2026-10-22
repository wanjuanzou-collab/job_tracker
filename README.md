# 计算任务 · 静态版

无需后端、数据库或依赖。打开 index.html 即可使用，或在此目录运行
`python -m http.server 8000 --bind 127.0.0.1` 后通过静态服务器访问。

支持搜索、状态筛选、待处理筛选、新建、编辑，以及 JSON 备份与恢复。
27 条初始记录在 records.js。修改保存在当前浏览器的 localStorage，刷新后保留；
不同设备、浏览器和网址之间不自动同步。清除网站数据会清除修改，重要修改请备份。
已有浏览器记录不会被新版初始数据覆盖。

## GitHub Pages

将这些文件推送到 main。在 GitHub 仓库 Settings → Pages → Build and deployment
选择 GitHub Actions。仓库中的 Publish static tracker 工作流会发布网站，成功后在
Settings → Pages 查看真实网址。尚未发布时不要把预计网址当作可用地址。

公开发布会使 records.js 中的计算路径、内容和结果可被访问；页面没有登录保护。
工作流只发布 index.html 和 records.js，不发布 Python 服务或 SQLite 文件。

server.py、data 和 tests 是早期后端版本，静态版不依赖它们。
