#!/usr/bin/env bash
# 给 Azure Static Web App 绑定自定义域名。
#
#   ./setup-domain.sh wenqili.net
#
# 会同时配置根域名 (wenqili.net) 和 www 子域名，
# 并打印你需要在注册商 DNS 面板里添加的记录。
# SWA Free 层最多 2 个自定义域名，正好够。
set -euo pipefail

APP=wenqi-li-website
RG=wenqi-website-rg

DOMAIN=${1:-}
if [ -z "$DOMAIN" ]; then
  echo "用法: ./setup-domain.sh <你的域名>   例如 ./setup-domain.sh wenqili.net" >&2
  exit 1
fi
DOMAIN=${DOMAIN#www.}

SWA_HOST=$(az staticwebapp show -n "$APP" -g "$RG" --query defaultHostname -o tsv)
echo "==> Static Web App: $SWA_HOST"
echo

# ---------- www 子域名：CNAME 验证 ----------
echo "==> 配置 www.$DOMAIN"
az staticwebapp hostname set -n "$APP" -g "$RG" \
   --hostname "www.$DOMAIN" --validation-method cname-delegation --no-wait -o none

# ---------- 根域名：TXT token 验证 ----------
echo "==> 配置 $DOMAIN（根域名，需 TXT 验证）"
az staticwebapp hostname set -n "$APP" -g "$RG" \
   --hostname "$DOMAIN" --validation-method dns-txt-token --no-wait -o none

echo "==> 等待 Azure 生成验证 token..."
TOKEN=""
for i in $(seq 1 20); do
  TOKEN=$(az staticwebapp hostname show -n "$APP" -g "$RG" --hostname "$DOMAIN" \
          --query validationToken -o tsv 2>/dev/null || true)
  [ -n "$TOKEN" ] && [ "$TOKEN" != "None" ] && break
  sleep 5
done

cat <<TXT

────────────────────────────────────────────────────────────────
请在注册商的 DNS 面板添加以下记录：

  1) 类型 CNAME   名称 www          值 $SWA_HOST

  2) 类型 TXT     名称 @            值 ${TOKEN:-（token 还没生成，稍后跑 ./domain-status.sh 查看）}

  3) 根域名指向（二选一，看你的 DNS 服务商支持哪种）：
     · 支持 ALIAS / ANAME / CNAME 展平（Cloudflare、Porkbun 都支持）：
         类型 ALIAS(或 CNAME)  名称 @  值 $SWA_HOST
     · 只支持 A 记录：
         类型 A  名称 @  值 $(dig +short "$SWA_HOST" | tail -1)
       （注意：这个 IP 未来可能变，能用 ALIAS 就别用 A）

如果用 Cloudflare：先把这几条记录设成 "DNS only"（灰云），
等证书签发成功后再决定要不要开代理（橙云）——
代理开着会干扰 Azure 的证书验证。
────────────────────────────────────────────────────────────────

DNS 生效后（几分钟到几小时），跑 ./domain-status.sh 查看验证和证书状态。
TXT
