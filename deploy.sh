#!/bin/bash
# ============================================================
# Talent Discovery Widget — 阿里云服务器部署脚本
# 在服务器上以 root 执行: bash deploy.sh
# ============================================================
set -e

PROJECT_DIR="/www/wwwroot/talent-discover-widget"
DOMAIN="talent.atgoertek.xyz"
PORT=8765

echo "=============================================="
echo " Talent Discovery Widget 部署"
echo "=============================================="

# 1. 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "[1/6] 安装 Python 3.11..."
    # CentOS/RHEL
    if command -v yum &> /dev/null; then
        yum install -y python3.11 python3.11-pip
        alternatives --set python3 /usr/bin/python3.11
    # Ubuntu/Debian
    elif command -v apt &> /dev/null; then
        apt update && apt install -y python3.11 python3.11-pip python3.11-venv
        update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
    fi
fi
echo "  Python: $(python3 --version)"

# 2. Clone / 拉取项目
echo "[2/6] 拉取项目代码..."
if [ -d "$PROJECT_DIR" ]; then
    cd "$PROJECT_DIR"
    git pull
else
    mkdir -p /www/wwwroot
    cd /www/wwwroot
    git clone https://github.com/ivan-cc-pool/talent-discover-widget.git
fi
cd "$PROJECT_DIR"

# 3. 安装 Python 依赖
echo "[3/6] 安装 Python 依赖..."
pip3 install -r requirements.txt

# 4. 配置环境变量
echo "[4/6] 配置环境变量..."
# SILICONFLOW_API_KEY 需要在宝塔面板或其他方式设置
read -p "请输入 SILICONFLOW_API_KEY: " SILICONFLOW_API_KEY
cat > /www/wwwroot/talent-discover-widget/.env << EOF
SILICONFLOW_API_KEY=${SILICONFLOW_API_KEY}
EOF
echo "  .env 文件已创建"

# 5. 创建 systemd 服务
echo "[5/6] 创建 systemd 服务..."
cat > /etc/systemd/system/talent-widget.service << EOF
[Unit]
Description=Talent Discovery Widget Backend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/www/wwwroot/talent-discover-widget
Environment="SILICONFLOW_API_KEY=${SILICONFLOW_API_KEY}"
ExecStart=/usr/bin/python3 -m uvicorn backend.server:app --host 127.0.0.1 --port ${PORT}
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable talent-widget
systemctl restart talent-widget
echo "  服务已启动，状态:"
systemctl status talent-widget --no-pager || true

# 6. 宝塔 Nginx 反向代理（手动步骤提示）
echo ""
echo "=============================================="
echo " [6/6] 后续手动操作："
echo "=============================================="
echo ""
echo " 1. 宝塔面板 → 网站 → 添加站点:"
echo "    域名: ${DOMAIN}"
echo "    根目录: /www/wwwroot/talent-discover-widget/widget/"
echo ""
echo " 2. SSL: 站点设置 → SSL → Let's Encrypt 一键申请"
echo ""
echo " 3. Nginx 反向代理（站点设置 → 配置文件 → 添加以下内容）:"
echo ""
cat << 'NGINX_TPL'
    # === WebSocket + API 反向代理 ===
    location /ws/ {
        proxy_pass http://127.0.0.1:8765;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }
    location /api/ {
        proxy_pass http://127.0.0.1:8765;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    location /demo {
        proxy_pass http://127.0.0.1:8765;
        proxy_set_header Host $host;
    }

NGINX_TPL
echo ""
echo " 4. Cloudflare DNS: 添加 A 记录"
echo "    talent.atgoertek.xyz → 服务器公网IP (橙色云朵可关闭以加速SSL)"
echo ""
echo "=============================================="
echo " 部署完成！"
echo "=============================================="
