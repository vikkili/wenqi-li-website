#!/usr/bin/env python3
"""从 photo/ 里的原图生成网页版相册，并更新 about.html。

用法：  python3 build-photos.py

原图按  事件'年@地点N.ext  命名，例如 CHI'26@Barcelona3.HEIC。
同一个「事件'年@地点」的照片自动归为一组。
生成物写到 photo/web/（该目录是自动生成的，不要手改）。

编号沿用原图的编号：删掉 Denmark3 之后，其余文件名保持不变，
这样已经上线的图片 URL 不会变，CDN 缓存也不会错位。
"""
import json, os, re, subprocess, sys, tempfile, unicodedata

from PIL import Image, ImageOps

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "photo")
OUT = os.path.join(SRC, "web")
FULL_MAX, THUMB_MAX, QUALITY = 1600, 640, 80

# 地点的中英文对照。新增地点请在这里补一行。
PLACES = {
    "Barcelona": ("Barcelona", "西班牙巴塞罗那"),
    "Yokohama":  ("Yokohama",  "日本横滨"),
    "HK":        ("Hong Kong", "中国香港"),
    "Denmark":   ("Denmark",   "丹麦"),
    "London":    ("London",    "英国伦敦"),
}

NAME = re.compile(r"^(?P<event>.+?)[‘’'](?P<year>\d{2})@(?P<place>[A-Za-z]+?)(?P<n>\d+)\.(?P<ext>\w+)$")


def capture_date(path):
    """拍摄时间，用于给相册组排序。取不到就返回空串。"""
    if path.lower().endswith((".jpg", ".jpeg")):
        try:
            ex = Image.open(path).getexif()
            d = ex.get(0x9003) or ex.get(0x0132)
            if d:
                return str(d)
        except Exception:
            pass
    out = subprocess.run(["sips", "-g", "creation", path],
                         capture_output=True, text=True).stdout
    m = re.search(r"creation:\s*(.+)", out)
    return m.group(1).strip() if m else ""


class _Desc:
    """让字符串在 sorted() 里按倒序参与比较。"""
    __slots__ = ("v",)

    def __init__(self, v):
        self.v = v

    def __lt__(self, other):
        return self.v > other.v

    def __eq__(self, other):
        return self.v == other.v


def scan():
    groups = {}
    unparsed = []
    for f in sorted(os.listdir(SRC)):
        p = os.path.join(SRC, f)
        if not os.path.isfile(p) or f.startswith(".") or f == "README.txt":
            continue
        m = NAME.match(unicodedata.normalize("NFC", f))
        if not m:
            unparsed.append(f)
            continue
        d = m.groupdict()
        key = (d["event"], d["year"], d["place"])
        groups.setdefault(key, []).append((int(d["n"]), f))
    return groups, unparsed


def to_jpeg(src, tmp):
    """HEIC 等格式先用 sips 转成 JPEG（Pillow 读不了 HEIC）。"""
    if src.lower().endswith((".jpg", ".jpeg")):
        return src
    subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "100",
                    src, "--out", tmp], check=True, capture_output=True)
    return tmp


def convert(src_jpeg, dst, max_px):
    """缩放到 max_px 以内，写出 JPEG。

    sips 不会把 EXIF 的 orientation 烘进像素，只是保留标签让浏览器旋转。
    这里先用 exif_transpose 把旋转落到像素上，再整体丢掉 EXIF ——
    否则剥掉标签后竖图会躺倒。同时也顺手去掉了 GPS、机型等元数据。
    """
    with Image.open(src_jpeg) as im:
        im = ImageOps.exif_transpose(im)
        if im.mode != "RGB":
            im = im.convert("RGB")
        im.thumbnail((max_px, max_px), Image.LANCZOS)
        im.save(dst, "JPEG", quality=QUALITY, optimize=True, progressive=True)


def main():
    groups, unparsed = scan()
    if unparsed:
        print("⚠️  这些文件名解析不了，已跳过：")
        for f in unparsed:
            print("     ", f)
    if not groups:
        sys.exit("photo/ 里没有找到可用的原图。")

    missing = {k[2] for k in groups} - set(PLACES)
    if missing:
        sys.exit(f"❌ 这些地点还没有中英文对照，请先在 build-photos.py 的 PLACES 里补上： {sorted(missing)}")

    os.makedirs(OUT, exist_ok=True)
    keep = set()
    manifest = []

    def group_key(k):
        latest = max((capture_date(os.path.join(SRC, f)) for _, f in groups[k]), default="")
        return (-int(k[1]), _Desc(latest), k[0])

    # 年份倒序；同年按该组最晚拍摄时间倒序（JCDL 12 月排在 ISIC 8 月之前）
    for (event, year, place) in sorted(groups, key=group_key):
        photos = sorted(groups[(event, year, place)])
        slug = re.sub(r"[^a-z0-9]", "", event.lower()) + year + "-" + place.lower()
        entry = {"slug": slug, "event": event, "year": year, "place": place, "photos": []}
        for n, fname in photos:
            base = f"{slug}-{n}"
            full, thumb = f"{base}.jpg", f"{base}-t.jpg"
            with tempfile.TemporaryDirectory() as td:
                jpg = to_jpeg(os.path.join(SRC, fname), os.path.join(td, "src.jpg"))
                convert(jpg, os.path.join(OUT, full), FULL_MAX)
                convert(jpg, os.path.join(OUT, thumb), THUMB_MAX)
            keep.update({full, thumb})
            entry["photos"].append({"full": f"photo/web/{full}", "thumb": f"photo/web/{thumb}"})
            print(f"  {fname}  ->  {full} + {thumb}")
        manifest.append(entry)

    # 清掉已删除照片留下的旧文件
    removed = []
    for f in sorted(os.listdir(OUT)):
        if f.endswith(".jpg") and f not in keep:
            os.remove(os.path.join(OUT, f))
            removed.append(f)
    if removed:
        print("\n已删除过期文件：")
        for f in removed:
            print("     ", f)

    keep.add("manifest.json")
    with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=1)

    update_about(manifest)
    total = sum(len(g["photos"]) for g in manifest)
    print(f"\n✅ {len(manifest)} 组、{total} 张照片；about.html 已更新。")


def update_about(manifest):
    path = os.path.join(ROOT, "about.html")
    s = open(path, encoding="utf-8").read()

    buttons, G = [], {}
    for g in manifest:
        slug, place = g["slug"], g["place"]
        place_en, place_zh = PLACES[place]
        title = f"{g['event']} ’{g['year']}"
        n = len(g["photos"])
        noun = "photo" if n == 1 else "photos"
        pile = "\n".join(
            f'          <img class="pile-img" src="{p["thumb"]}" alt="" loading="lazy">'
            for p in reversed(g["photos"][:3]))
        buttons.append(
            f'      <button class="stack" type="button" data-group="{slug}"'
            f' aria-label="{g["event"]} {g["year"]}, {place_en} — {n} {noun}">\n'
            f'        <span class="pile">\n{pile}\n        </span>\n'
            f'        <span class="stack-cap">\n'
            f'          <span class="stack-title">{title}</span>\n'
            f'          <span class="stack-sub"><span class="lang-en">{place_en} · {n} {noun}</span>'
            f'<span class="lang-zh">{place_zh} · {n} 张</span></span>\n'
            f'        </span>\n'
            f'      </button>')
        G[slug] = {"title": title, "place_en": place_en, "place_zh": place_zh,
                   "photos": [p["full"] for p in g["photos"]]}

    grid = '    <div class="stack-grid">\n' + "\n".join(buttons) + "\n    </div>"
    new, cnt = re.subn(r'    <div class="stack-grid">.*?\n    </div>', lambda _: grid, s, count=1, flags=re.S)
    assert cnt == 1, "about.html 里没找到 stack-grid 区块"

    gline = "  var G=" + json.dumps(G, ensure_ascii=False) + ";"
    new, cnt = re.subn(r"^  var G=\{.*?\};$", lambda _: gline, new, count=1, flags=re.M)
    assert cnt == 1, "about.html 里没找到 var G 定义"

    open(path, "w", encoding="utf-8").write(new)


if __name__ == "__main__":
    main()
