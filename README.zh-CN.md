# Color Number 数字填色

[English](README.md) | **中文**

把照片变成像素格子，再按编号一格一格填色的小游戏。用 Python 和 Kivy 编写。

游戏默认是英文界面，在 **Settings → Language** 里选"中文"即可切换。

## 功能

- **内置图库**：蘑菇、橘猫、草莓、冰淇淋、小房子、仙人掌、小丑鱼、湖边日落
- **导入照片**（JPG / PNG / iPhone 的 HEIC 等）：裁剪，调整亮度、对比度、饱和度，自由选择格子数和颜色数，实时预览，一键恢复默认
  - **三种风格**：**平滑**（默认，颜色过渡柔和，边界圆润没有尖角）、**清晰**（锐化边缘，细节最多）、**经典**（第一版的算法）
  - **对比原图**：拖动分隔线左右对比原图和填色图，并显示"还原度"，看出调整和转换让图片变了多少
  - 都在 Lab 颜色空间里选色（颜色更好区分），眼白、嘴唇、高光这类小而显眼的颜色会单独留出名额
  - **推荐颜色数**：为每张图算出一个"能还原、颜色又好区分"的颜色数，一键使用；颜色太接近时会提醒
  - **AI 识别**（macOS）：用系统自带的 Apple Vision 离线识别人脸、五官和主体，五官保留更多细节，还可以一键虚化背景
- **填色**：点击或拖动上色，笔刷可选 1×1、3×3、5×5；滚轮或触控板捏合缩放，触控板双指滑动移动画布；远看是灰色轮廓，放大后渐变成白底和编号
- **辅助工具**（都可以无限使用）：高亮当前编号、魔棒（填满相连的同编号区域）、油漆桶（填满整张图的同一编号；**长按**一键填完整张图）、提示（自动移动到还没填的格子并闪烁）、吸管（Option + 点击选中这一格的颜色）、撤销（步数不限，关闭程序后仍然保留）和重做
- **颜色栏**：显示每种颜色的剩余进度，填完打勾，并自动跳到下一种颜色
- **完成之后**：彩带庆祝和填色过程快速回放；可以导出 PNG 图片、GIF 动图、MP4 视频
- **作品集**：按"进行中/已完成"筛选，可以继续、重命名、重新开始、导出、删除；进度自动保存
- **背景音乐**：8 首网上精选的轻松音乐（CC0 授权，见下文）+ 5 首代码合成的音乐，随机播放，可以切下一首；可以**导入自己的音乐**（MP3、OGG、FLAC、WAV、M4A 等），并选择只放某一类
- **音效**（代码合成）：填色时"啵"的音效会按五声音阶往上走，填错有单独的提示音
- **设置**：中英文切换、填错时的处理方式（不让填，或填上但标为错误）、更大的格子和颜色上限、音效和音乐的开关与音量

## 下载就能玩（macOS）

最简单的方式：下载打包好的 App，不需要安装 Python。

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

Intel 芯片的 Mac、Windows、Linux 请用下面"从源码运行"的方式。

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
packaging/build_macos.sh 1.0.0
```

打包好的 App 和用来上传到 GitHub Releases 的 zip 会出现在 `dist/` 文件夹。打包使用 PyInstaller，不附带 ffmpeg。

## 操作方法

| 操作 | 鼠标 / 键盘 |
|---|---|
| 填色 | 左键点击或拖动 |
| 缩放 | 触控板捏合、滚轮，或按 `+` / `-` |
| 移动画布 | 触控板双指滑动、右键拖动、按住空格再拖动、"移动"工具，或方向键 |
| 吸管（选中某格的颜色） | 按住 `Option`（Windows 上是 `Alt`）点击格子 |
| 撤销 / 重做 | `Cmd+Z` / `Cmd+Shift+Z`（Windows 上是 `Ctrl+Z` / `Ctrl+Y`） |
| 笔刷大小 | `[` 变小，`]` 变大 |
| 一键填完整张图 | 长按"油漆桶"按钮 |
| 提示 | `H` |
| 切换工具 | `B` 画笔、`W` 魔棒、`M` 移动 |
| 显示全图 | `0` |

触屏设备上：一根手指填色，两根手指缩放和移动。

## 文件存放位置

- 作品存档和设置：`~/Library/Application Support/colornumber/`（macOS）
- 导出的图片和视频：`~/Pictures/Color Number/`

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
    library.py           内置图库（字符画）
    render.py            把进度画成图片
    export.py            导出 PNG / GIF / MP4
    audio.py             合成音效和背景音乐
    i18n.py              中英文界面文字
  assets/music/          精选音乐（OGG）和 credits.json（作者、许可证、来源）
  ui/                    Kivy 界面
    app.py               管理各个页面
    paint_canvas.py      可以缩放的填色画布
    game_screen.py       填色页面
    home_screen.py       首页：图库和作品集
    import_screen.py     导入照片页面
    settings_screen.py   设置页面
    common.py            按钮、弹窗、字体等公共部分
    mac_gestures.py      Mac 触控板手势（捏合缩放、双指滑动）
    sound.py / confetti.py / exporting.py
packaging/               打包 macOS App 的脚本（PyInstaller）
preview.py               不打开游戏，只在命令行预览照片转换的效果
tests/                   自动测试（运行 pytest）
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
