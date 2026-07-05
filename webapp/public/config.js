// 运行时配置占位 —— 本地 dev 为空（走 MSW mock）；
// 部署容器 entrypoint 会用环境变量覆盖此文件（docker/Dockerfile.webapp）。
window.__AP_CONFIG__ = {};
