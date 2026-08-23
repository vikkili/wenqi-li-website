#!/usr/bin/env bash
# 查看自定义域名的验证 / 证书状态
set -euo pipefail
APP=wenqi-li-website
RG=wenqi-website-rg
echo "默认域名: $(az staticwebapp show -n "$APP" -g "$RG" --query defaultHostname -o tsv)"
echo
n=$(az staticwebapp hostname list -n "$APP" -g "$RG" --query 'length(@)' -o tsv 2>/dev/null || echo 0)
if [ "$n" = "0" ]; then
  echo "尚未绑定任何自定义域名。买好域名后跑： ./setup-domain.sh <域名>"
else
  az staticwebapp hostname list -n "$APP" -g "$RG" \
    --query '[].{hostname:name, status:status, method:validationMethod, token:validationToken}' -o table
fi
