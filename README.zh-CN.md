# Color Number 数字填色

[English](README.md) | **中文**

把照片变成像素格子，再按编号一格一格填色的小游戏。用 Python 和 Kivy 编写。

游戏默认是英文界面，在 **Settings → Language** 里选"中文"即可切换。

## 功能

- **内置图库**：24 张图，分成动物、美食、自然、物品四类，从橘猫、企鹅到甜甜圈、星空湖畔和灯塔
- **名画**：内置 27 幅中外名画，**不用联网**（在中国大陆也能用），来自大都会艺术博物馆（CC0）和国立故宫博物院（台北，CC BY 4.0），署名完整；也可以在线搜索[芝加哥艺术博物馆](https://www.artic.edu)公有领域（CC0）的油画和版画
- **导入照片**（JPG / PNG / iPhone 的 HEIC 等）：裁剪，调整亮度、对比度、饱和度，自由选择格子数和颜色数，实时预览，一键恢复默认
  - **三种风格**：**平滑**（默认，颜色过渡柔和，边界圆润没有尖角）、**清晰**（锐化边缘，细节最多）、**经典**（第一版的算法）
  - **对比原图**：拖动分隔线左右对比原图和填色图，并显示"还原度"，看出调整和转换让图片变了多少
  - 都在 Lab 颜色空间里选色（颜色更好区分），眼白、嘴唇、高光这类小而显眼的颜色会单独留出名额
  - **推荐颜色数**：为每张图算出一个"能还原、颜色又好区分"的颜色数，一键使用；颜色太接近时会提醒
  - **AI 识别**（macOS）：用系统自带的 Apple Vision 离线识别人脸、五官和主体，五官保留更多细节，还可以一键虚化背景
- **填色**：点击或拖动上色，笔刷可选 1×1、3×3、5×5；滚轮或触控板捏合缩放，触控板双指滑动移动画布；远看是灰色轮廓，放大后渐变成白底和编号
- **辅助工具**（都可以无限使用）：高亮当前编号、魔棒（填满相连的同编号区域）、油漆桶（填满整张图的同一编号；**长按**一键填完整张图）、提示（自动移动到还没填的格子并闪烁）、吸管（Option + 点击选中这一格的颜色）、撤销和重画（把撤销的笔画画回来）：步数不限，关闭程序后仍然保留；没有可撤销或重画的笔画时按钮会变淡
- **颜色栏**：显示每种颜色的剩余进度，填完打勾，并自动跳到下一种颜色
- **完成之后**：彩带庆祝和填色过程快速回放；可以导出 PNG 图片、GIF 动图、MP4 视频
- **作品集**：按"进行中/已完成"筛选，可以继续、重命名、重新开始、导出、删除；进度自动保存
- **隐藏图片**：图库和我的作品里不想看到的图，可以在卡片的"…"菜单里隐藏。不会删除，点"显示已隐藏"就能找回来
- **背景音乐**：8 首网上精选的轻松音乐（CC0 授权，见下文）+ 5 首代码合成的音乐，随机播放，可以切下一首，也可以在设置里的歌单直接点选一首；可以**导入自己的音乐**（MP3、OGG、FLAC、WAV、M4A 等），并选择只放某一类
- **音效**（代码合成）：填色时"啵"的音效会按五声音阶往上走，填错有单独的提示音
- **设置**：中英文切换、填错时的处理方式（不让填，或填上但标为错误）、更大的格子和颜色上限、音效和音乐的开关与音量

## 在手机上玩（iPhone 和 Android）

在手机上打开 **https://sanitysr163216.github.io/pixel-color-by-number/** ，然后添加到主屏幕：

- **iPhone / iPad**：在 Safari 里点"分享"按钮，再点 **添加到主屏幕**。
- **Android**：在 Chrome 里点右上角的菜单，再点 **安装应用**（或 **添加到主屏幕**）。

之后就像 App 一样从主屏幕打开，没有网络也能玩，进度保存在手机里。免费，也不会过期。
手机版有内置图库、触摸填色（一根手指填色，两根手指缩放和移动）、撤销/重画、魔棒、油漆桶、提示、隐藏图片，
还能导入照片，转换算法和电脑版完全一样（第一次导入照片时要下载约 17 MB 的转换工具）。
完成的图可以通过"分享"存成 PNG。

## 下载就能玩

在电脑上最简单的方式：下载打包好的 App，不需要安装 Python。

### macOS

1. 打开[最新发布页面](https://github.com/Sanitysr163216/pixel-color-by-number/releases/latest)，
   下载 `Color-Number-<版本>-macOS-arm64.zip`。
   适用于 Apple 芯片（M1 及以后）的 Mac，需要 macOS 12 或更新版本。
2. 双击 zip 解压，把 **Color Number.app** 拖进"应用程序"文件夹。
3. 打开它。第一次打开时，macOS 会提示"无法验证开发者"，因为这个 App 没有用付费的苹果开发者证书签名。允许的方法：
   - 在提示框里点"完成"（或"好"）。
   - 打开 **系统设置 → 隐私与安全性**，往下找到"Color Number"，点 **仍要打开**，再用密码或触控 ID 确认。
   - 以后就能正常打开了。

下载版可以导出 PNG 和 GIF。导出 MP4 需要 [ffmpeg](https://ffmpeg.org)：
用 Homebrew 安装（`brew install ffmpeg`）之后，MP4 按钮会自动出现。

### Windows

1. 打开[最新发布页面](https://github.com/Sanitysr163216/pixel-color-by-number/releases/latest)，
   下载 `Color-Number-<版本>-Windows-x64.zip`。适用于 64 位的 Windows 10 和 11。
2. 右键点 zip → **全部解压缩…**，选一个位置放 **Color Number** 文件夹。
3. 打开文件夹，双击 **Color Number.exe**。第一次打开时 Windows 可能提示"Windows 已保护你的电脑"，
   因为这个程序没有用付费证书签名。点 **更多信息 → 仍要运行** 即可，以后就能正常打开。
   小技巧：右键 **Color Number.exe → 显示更多选项 → 发送到 → 桌面快捷方式**。

Windows 版可以导出 PNG 和 GIF，可以导入 MP3、OGG、FLAC、WAV 格式的音乐。
想导出 MP4 或导入其他格式的音乐（M4A、AAC……），请安装 [ffmpeg](https://ffmpeg.org)，
比如在终端里运行 `winget install ffmpeg`，然后重新打开游戏。

Intel 芯片的 Mac 和 Linux 请用下面"从源码运行"的方式。

## 从源码运行

适合想看代码、改代码的人，或者没有现成 App 的电脑。第 1–4 步只需要做一次。

1. **安装 Miniforge**（一个小巧的 Python 发行版）：
   [github.com/conda-forge/miniforge](https://github.com/conda-forge/miniforge#install)。
   装好后关掉终端，再重新打开。
2. **下载代码**：在本页点绿色的 **Code** 按钮 → **Download ZIP** 并解压；或者用 git：

   ```bash
   git clone https://github.com/Sanitysr163216/pixel-color-by-number.git
   ```

3. **在终端里进入项目文件夹**：输入 `cd `（后面带一个空格），把解压出来的文件夹拖进终端窗口，按回车。
   Windows 上请用开始菜单里的 **Miniforge Prompt** 当终端。
4. **创建环境**（要下载约 1 GB，需要几分钟）：

   ```bash
   conda env create --file environment.yml
   ```

5. **启动游戏**：

   ```bash
   conda activate color-number
   python main.py
   ```

以后每次只需要第 5 步。在 macOS 上也可以直接双击项目文件夹里的 **Color Number.app**：
它是一个小启动器，会用 `color-number` 环境运行 `main.py`（请把它留在项目文件夹里，可以拖到程序坞做快捷方式）。
更新代码后，运行 `conda env update --file environment.yml` 同步环境。

### 自己打包 App（macOS）

```bash
conda activate color-number
conda install -c conda-forge pyinstaller     # 只需要装一次
packaging/build_macos.sh
```

版本号写在 `colornumber/__init__.py` 里。打包好的 App 和用来上传到 GitHub Releases 的 zip 会出现在 `dist/` 文件夹。打包使用 PyInstaller，不附带 ffmpeg。

### 生成网页版（手机版）

手机版的代码在 `web/` 文件夹（HTML、CSS、JavaScript）。`packaging/build_web.py` 把它复制到 `site/`，
同时从 Python 代码导出内置图、界面文字和图标，所以两个版本用的是同一份。
照片转换在浏览器里用 [Pyodide](https://pyodide.org) 运行原封不动的 `converter.py`。

```bash
python packaging/build_web.py
python -m http.server --directory site 8000      # 然后打开 http://localhost:8000
```

[`web.yml`](.github/workflows/web.yml) 会在每次推送到 `main` 时自动生成并发布到 GitHub Pages。

### 打包 Windows 版

PyInstaller 只能在 Windows 上打包 Windows 程序。GitHub Actions 的
[`windows.yml`](.github/workflows/windows.yml) 会自动完成：运行测试、自动试玩一遍、打包出
`Color-Number-<版本>-Windows-x64.zip`，推送 `v` 开头的 tag 时还会把它加到那个版本的下载里。
也可以在 GitHub 网页的 **Actions → Windows build → Run workflow** 手动运行。

在自己的 Windows 电脑上打包（PowerShell，需要 Python 3.12）：

```powershell
pip install -r packaging/requirements-windows.txt
packaging/build_windows.ps1
```

## 操作方法

| 操作 | 鼠标 / 键盘 |
|---|---|
| 填色 | 左键点击或拖动 |
| 缩放 | 触控板捏合、滚轮，或按 `+` / `-` |
| 移动画布 | 触控板双指滑动、右键拖动、按住空格再拖动、"移动"工具，或方向键 |
| 吸管（选中某格的颜色） | 按住 `Option`（Windows 上是 `Alt`）点击格子 |
| 撤销 / 重画 | `Cmd+Z` / `Cmd+Shift+Z`（Windows 上是 `Ctrl+Z` / `Ctrl+Y`） |
| 笔刷大小 | `[` 变小，`]` 变大 |
| 一键填完整张图 | 长按"油漆桶"按钮 |
| 提示 | `H` |
| 切换工具 | `B` 画笔、`W` 魔棒、`M` 移动 |
| 显示全图 | `0` |
| 全屏 | `Ctrl+Cmd+F` 或 `F11`（Windows 上是 `F11`） |

触屏设备上：一根手指填色，两根手指缩放和移动。

## 文件存放位置

- 作品存档和设置：`~/Library/Application Support/colornumber/`（macOS），`%APPDATA%\colornumber\`（Windows）
- 导出的图片和视频：个人文件夹里的 `Pictures/Color Number`（Windows 上是"图片"文件夹）

## 项目结构

```
main.py                  程序入口
colornumber/
  core/                  纯 Python 的游戏逻辑，不引用 Kivy（以后移植 iPhone 时可以直接复用）
    picture.py           一张填色图的数据（调色板 + 编号格子）
    converter.py         照片 → 填色图（Lab 选色、锐化、推荐颜色数）
    vision.py            AI 识别人脸、五官和主体（Apple Vision，只在 macOS 上）
    music.py             背景音乐曲库：精选音乐和"我的音乐"（导入、转换格式、删除）
    game.py              填色进度、魔棒、油漆桶、撤销、提示、回放
    storage.py           作品存档
    settings.py          设置
    library.py           内置图库（字符画）和分类
    library_more.py      第二批内置图（用简单形状画出来）
    online.py            在线名画搜索（芝加哥艺术博物馆的接口）
    artworks.py          内置名画包（不用联网）
    render.py            把进度画成图片
    export.py            导出 PNG / GIF / MP4
    audio.py             合成音效和背景音乐
    i18n.py              中英文界面文字
  assets/music/          精选音乐（OGG）和 credits.json（作者、许可证、来源）
  assets/artworks/       内置名画和 credits.json（署名、授权、来源）
  ui/                    Kivy 界面
    app.py               管理各个页面
    paint_canvas.py      可以缩放的填色画布
    game_screen.py       填色页面
    home_screen.py       首页：图库和作品集
    online_screen.py     名画页面（内置名画和在线搜索）
    icons.py             工具栏的像素小图标
    pickers.py           选择文件的窗口（macOS、Windows 用系统自己的）
    import_screen.py     导入照片页面
    settings_screen.py   设置页面
    common.py            按钮、弹窗、字体等公共部分
    mac_gestures.py      Mac 触控板手势（捏合缩放、双指滑动）
    sound.py / confetti.py / exporting.py
packaging/               打包脚本：macOS 和 Windows 版（PyInstaller）、网页版
web/                     手机版 / 网页版（PWA）：HTML、CSS、JavaScript
.github/workflows/       在 GitHub 的 Windows 电脑上测试和打包
preview.py               不打开游戏，只在命令行预览照片转换的效果
tests/                   自动测试（运行 pytest）；ui_smoke.py 会真的打开游戏自动点一遍
exercises/               Python 练习（见下文）
```

## 测试

```bash
pytest
```

## 练习

`exercises/` 文件夹里是配合这个项目的 Python 练习：打开 `progress.py` 写函数，然后运行 `check_my_functions.py` 检查。

## 关于 iPhone 版

游戏逻辑（`colornumber/core`）和界面分开编写，Kivy 也支持 iOS，所以以后可以用 [kivy-ios](https://github.com/kivy/kivy-ios) 打包到 iPhone 上（需要 Mac 和 Xcode）。到时候需要调整的地方：

- 选择照片：改用 iOS 的相册选择器
- 中文字体：改用 iOS 系统字体的路径（或者随应用附带一个开源中文字体）
- 导出 MP4：iPhone 上没有 ffmpeg，需要换一种方式
- AI 识别：iOS 也有 Vision 框架，但要改用 kivy-ios 的 pyobjus 来调用
- 布局：适配竖屏和小屏幕

## 内置名画的来源

`colornumber/assets/artworks/` 里的内置名画来自两个开放资料库：
[大都会艺术博物馆](https://www.metmuseum.org/hubs/open-access)（公有领域，CC0）和
[国立故宫博物院（台北）](https://digitalarchive.npm.gov.tw/opendata)（CC BY 4.0，按院方规定的格式署名）。
游戏里的图已经缩小，部分裁掉了照片边上的色卡和空白的对页。
`packaging/fetch_artworks.py` 负责下载和整理，游戏里显示的署名在 `credits.json` 里。

| 作品 | 作者 | 署名与授权 |
|---|---|---|
| [神奈川冲浪里](https://www.metmuseum.org/art/collection/search/45434) | 葛饰北斋，约1830–1832年 | Under the Wave off Kanagawa (Kanagawa oki nami ura), also known as The Great Wave, from the series Thirty-six Views of Mount Fuji (Fugaku sanjūrokkei), Katsushika Hokusai, ca. 1830–32. The Metropolitan Museum of Art, H. O. Havemeyer Collection, Bequest of Mrs. H. O. Havemeyer, 1929. Public domain (CC0).（大都会艺术博物馆，公有领域 CC0） |
| [照夜白图](https://www.metmuseum.org/art/collection/search/39901) | 韩幹，唐，约750年 | Night-Shining White, Han Gan, ca. 750. The Metropolitan Museum of Art, Purchase, The Dillon Fund Gift, 1977. Public domain (CC0).（大都会艺术博物馆，公有领域 CC0） |
| [王羲之观鹅图](https://www.metmuseum.org/art/collection/search/40081) | 钱选，元，约1295年 | Wang Xizhi watching geese, Qian Xuan, ca. 1295. The Metropolitan Museum of Art, Ex coll.: C. C. Wang Family, Gift of The Dillon Fund, 1973. Public domain (CC0).（大都会艺术博物馆，公有领域 CC0） |
| [竹禽图](https://www.metmuseum.org/art/collection/search/39936) | 宋徽宗，北宋，12世纪初 | Finches and bamboo, Emperor Huizong, early 12th century. The Metropolitan Museum of Art, John M. Crawford Jr. Collection, Purchase, Douglas Dillon Gift, 1981. Public domain (CC0).（大都会艺术博物馆，公有领域 CC0） |
| [月下赏梅图](https://www.metmuseum.org/art/collection/search/44638) | 马远，南宋，13世纪初 | Viewing plum blossoms by moonlight, Ma Yuan, early 13th century. The Metropolitan Museum of Art, Gift of John M. Crawford Jr., in honor of Alfreda Murck, 1986. Public domain (CC0).（大都会艺术博物馆，公有领域 CC0） |
| [兰花图](https://www.metmuseum.org/art/collection/search/40133) | 马麟，南宋，13世纪 | Orchids, Ma Lin, second quarter of the 13th century. The Metropolitan Museum of Art, Ex coll.: C. C. Wang Family, Gift of The Dillon Fund, 1973. Public domain (CC0).（大都会艺术博物馆，公有领域 CC0） |
| [双喜图](https://digitalarchive.npm.gov.tw/opendata/Pub/Detail/48?dep=P&mode=full) | 崔白，北宋，1061年 | 宋崔白雙喜圖 軸。國立故宮博物院，台北，CC BY 4.0 @ www.npm.gov.tw |
| [仙萼长春·牡丹](https://digitalarchive.npm.gov.tw/opendata/Pub/Detail/4954?dep=P&mode=full) | 郎世宁，清 | 清郎世寧畫仙萼長春 冊 牡丹。國立故宮博物院，台北，CC BY 4.0 @ www.npm.gov.tw |
| [仙萼长春·虞美人蝴蝶花](https://digitalarchive.npm.gov.tw/opendata/Pub/Detail/4958?dep=P&mode=full) | 郎世宁，清 | 清郎世寧畫仙萼長春 冊 虞美人蝴蝶花。國立故宮博物院，台北，CC BY 4.0 @ www.npm.gov.tw |
| [聚瑞图](https://digitalarchive.npm.gov.tw/opendata/Pub/Detail/3581?dep=P&mode=full) | 郎世宁，清，1723年 | 清郎世寧聚瑞圖 軸。國立故宮博物院，台北，CC BY 4.0 @ www.npm.gov.tw |
| [岁朝图](https://digitalarchive.npm.gov.tw/opendata/Pub/Detail/1227?dep=P&mode=full) | 赵昌，宋 | 宋趙昌歲朝圖 軸。國立故宮博物院，台北，CC BY 4.0 @ www.npm.gov.tw |
| [宫乐图](https://digitalarchive.npm.gov.tw/opendata/Pub/Detail/5?dep=P&mode=full) | 唐人（佚名），唐 | 唐人宮樂圖 軸。國立故宮博物院，台北，CC BY 4.0 @ www.npm.gov.tw |
| [秋庭戏婴图](https://digitalarchive.npm.gov.tw/opendata/Pub/Detail/34?dep=P&mode=full) | 苏汉臣，宋 | 宋蘇漢臣秋庭戲嬰圖 軸。國立故宮博物院，台北，CC BY 4.0 @ www.npm.gov.tw |
| [谿山行旅图](https://digitalarchive.npm.gov.tw/opendata/Pub/Detail/1195?dep=P&mode=full) | 范宽，北宋 | 宋范寬谿山行旅圖 軸。國立故宮博物院，台北，CC BY 4.0 @ www.npm.gov.tw |
| [早春图](https://digitalarchive.npm.gov.tw/opendata/Pub/Detail/47?dep=P&mode=full) | 郭熙，北宋，1072年 | 宋郭熙早春圖 軸。國立故宮博物院，台北，CC BY 4.0 @ www.npm.gov.tw |
| [十骏犬·雪爪卢](https://digitalarchive.npm.gov.tw/opendata/Pub/Detail/13636?dep=P&mode=full) | 郎世宁，清 | 清郎世寧畫十駿犬雪爪盧 軸。國立故宮博物院，台北，CC BY 4.0 @ www.npm.gov.tw |
| [麦田与柏树](https://www.metmuseum.org/art/collection/search/436535) | 文森特·梵高，1889年 | Wheat Field with Cypresses, Vincent van Gogh, 1889. The Metropolitan Museum of Art, Purchase, The Annenberg Foundation Gift, 1993. Public domain (CC0).（大都会艺术博物馆，公有领域 CC0） |
| [向日葵](https://www.metmuseum.org/art/collection/search/436524) | 文森特·梵高，1887年 | Sunflowers, Vincent van Gogh, 1887. The Metropolitan Museum of Art, Rogers Fund, 1949. Public domain (CC0).（大都会艺术博物馆，公有领域 CC0） |
| [鸢尾花](https://www.metmuseum.org/art/collection/search/436528) | 文森特·梵高，1890年 | Irises, Vincent van Gogh, 1890. The Metropolitan Museum of Art, Gift of Adele R. Levy, 1958. Public domain (CC0).（大都会艺术博物馆，公有领域 CC0） |
| [戴草帽的自画像](https://www.metmuseum.org/art/collection/search/436532) | 文森特·梵高，1887年 | Self-Portrait with a Straw Hat (obverse: The Potato Peeler), Vincent van Gogh, 1887. The Metropolitan Museum of Art, Bequest of Miss Adelaide Milton de Groot (1876-1967), 1967. Public domain (CC0).（大都会艺术博物馆，公有领域 CC0） |
| [夹竹桃](https://www.metmuseum.org/art/collection/search/436530) | 文森特·梵高，1888年 | Oleanders, Vincent van Gogh, 1888. The Metropolitan Museum of Art, Gift of Mr. and Mrs. John L. Loeb, 1962. Public domain (CC0).（大都会艺术博物馆，公有领域 CC0） |
| [柏树](https://www.metmuseum.org/art/collection/search/437980) | 文森特·梵高，1889年 | Cypresses, Vincent van Gogh, 1889. The Metropolitan Museum of Art, Rogers Fund, 1949. Public domain (CC0).（大都会艺术博物馆，公有领域 CC0） |
| [持水壶的年轻女子](https://www.metmuseum.org/art/collection/search/437881) | 约翰内斯·维米尔，约1662年 | Young Woman with a Water Pitcher, Johannes Vermeer, ca. 1662. The Metropolitan Museum of Art, Marquand Collection, Gift of Henry G. Marquand, 1889. Public domain (CC0).（大都会艺术博物馆，公有领域 CC0） |
| [收割者](https://www.metmuseum.org/art/collection/search/435809) | 老彼得·勃鲁盖尔，1565年 | The Harvesters, Pieter Bruegel the Elder, 1565. The Metropolitan Museum of Art, Rogers Fund, 1919. Public domain (CC0).（大都会艺术博物馆，公有领域 CC0） |
| [舞蹈课](https://www.metmuseum.org/art/collection/search/438817) | 埃德加·德加，1874年 | The Dance Class, Edgar Degas, 1874. The Metropolitan Museum of Art, Bequest of Mrs. Harry Payne Bingham, 1986. Public domain (CC0).（大都会艺术博物馆，公有领域 CC0） |
| [玛达·普里马维西](https://www.metmuseum.org/art/collection/search/436819) | 古斯塔夫·克里姆特，1912–1913年 | Mäda Primavesi (1903–2000), Gustav Klimt, 1912–13. The Metropolitan Museum of Art, Gift of André and Clara Mertens, in memory of her mother, Jenny Pulitzer Steiner, 1964. Public domain (CC0).（大都会艺术博物馆，公有领域 CC0） |
| [狮子的晚餐](https://www.metmuseum.org/art/collection/search/438822) | 亨利·卢梭，约1907年 | The Repast of the Lion, Henri Rousseau (le Douanier), ca. 1907. The Metropolitan Museum of Art, Bequest of Sam A. Lewisohn, 1951. Public domain (CC0).（大都会艺术博物馆，公有领域 CC0） |

## 精选音乐的来源

这 8 首音乐都来自 OpenGameArt 的 ["CC0 - Calm / Relaxing Music"](https://opengameart.org/content/cc0-calm-relaxing-music) 合集，
许可证都是 CC0（公有领域），可以自由使用和分发。下载后转成了 OGG 并统一了响度。感谢各位作者：

| 曲名 | 作者 | 来源 |
|---|---|---|
| Vaporware | cynicmusic（The Cynic Project） | [链接](https://opengameart.org/content/calm-piano-1-vaporware) |
| Good Morning | Cakeflaps @ You're Perfect Studio | [链接](https://opengameart.org/content/good-morning) |
| Another August | cynicmusic（The Cynic Project） | [链接](https://opengameart.org/content/another-august) |
| November Snow | cynicmusic（The Cynic Project） | [链接](https://opengameart.org/content/november-snow) |
| Serenade | Pro Sensory（Alex McCulloch） | [链接](https://opengameart.org/content/serenade-guitar) |
| Bossa Shop Theme | SpringySpringo | [链接](https://opengameart.org/content/bossa-shop-theme-in-low-fi-and-hd) |
| A Simple Trifle | jestar | [链接](https://opengameart.org/content/a-simple-trifle) |
| Menu Chill | etrock | [链接](https://opengameart.org/content/menu-chill-music) |

## 许可证

代码使用 [MIT 许可证](LICENSE)：任何人都可以免费使用、修改和分发，只需要保留版权声明。
`colornumber/assets/music/` 里的精选音乐是 CC0（公有领域），作者见上文。
`colornumber/assets/artworks/` 里的内置名画是 CC0（大都会艺术博物馆）或 CC BY 4.0（国立故宫博物院，台北），署名见上文。
