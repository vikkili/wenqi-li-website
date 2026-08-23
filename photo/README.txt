把新照片放在 photo/ 里，按 事件'年@地点N 命名，例如：

    CHI'26@Barcelona3.HEIC
    ISIC'24@Denmark10.jpg

同一个 label 的照片会自动归成一组（叠放 + 点开轮播）。
HEIC / JPG / PNG 都可以，原图多大都行。

加完照片后告诉 Claude 重新生成一次，它会：
  1. 转成 JPEG（HEIC 浏览器不支持）
  2. 压到网页尺寸，输出到 photo/web/
  3. 更新 about.html 里的相册数据

photo/web/ 是自动生成的，不要手动改。
