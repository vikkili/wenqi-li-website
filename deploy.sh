#!/usr/bin/env bash
# 部署到 Azure Static Web Apps。
# 需要先 az login（租户 a82c9fc8-1578-43ec-9302-b3f3e83acf22）。
set -euo pipefail

APP=wenqi-li-website
RG=wenqi-website-rg
STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT

cd "$(dirname "$0")"

# 只放该公开的文件，photo/ 下的原图不上传
mkdir -p "$STAGE/photo"
cp index.html about.html research.html teaching.html cv.html 404.html \
   favicon.svg photo.jpg Wenqi_Li_CV.pdf staticwebapp.config.json "$STAGE/"
cp -R photo/web "$STAGE/photo/"

echo "==> 待部署 $(find "$STAGE" -type f | wc -l | tr -d ' ') 个文件，$(du -sh "$STAGE" | cut -f1)"

TOKEN=$(az staticwebapp secrets list -n "$APP" -g "$RG" --query properties.apiKey -o tsv)
npx -y @azure/static-web-apps-cli@latest deploy "$STAGE" \
    --deployment-token "$TOKEN" --env production
