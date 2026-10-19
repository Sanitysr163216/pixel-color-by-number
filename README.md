# Color Number 数字填色

把照片变成像素格子，再按编号一格一格填色的小游戏。用 Python 和 Kivy 编写。

*A pixel-art color-by-number game written in Python with Kivy. Import any photo, turn it into a numbered grid, and paint it cell by cell.*

## 功能

- **内置图库**：蘑菇、橘猫、草莓、冰淇淋、小房子、仙人掌、小丑鱼、湖边日落
- **导入照片**（JPG / PNG / iPhone 的 HEIC 等）：裁剪，调整亮度、对比度、饱和度，自由选择格子数和颜色数，实时预览，自动清理杂色点
- **填色**：点击或拖动上色；滚轮缩放、拖动画布；远看是灰色轮廓，放大后渐变成白底和编号
- **辅助工具**（都可以无限使用）：高亮当前编号、魔棒（填满相连的同编号区域）、油漆桶（填满整张图的同一编号）、提示（自动移动到还没填的格子并闪烁）、撤销（步数不限，关闭程序后仍然保留）
- **颜色栏**：显示每种颜色的剩余进度，填完打勾，并自动跳到下一种颜色
- **完成之后**：彩带庆祝和填色过程快速回放；可以导出 PNG 图片、GIF 动图、MP4 视频
- **作品集**：按"进行中/已完成"筛选，可以继续、重新开始、导出、删除；进度自动保存
- **设置**：中英文切换、填错时的处理方式（不让填，或填上但标为错误）、更大的格子和颜色上限、音效和背景音乐（声音全部由代码合成）

## 安装和运行

需要先安装 [Miniforge](https://github.com/conda-forge/miniforge)（conda）。

```bash
conda env create --file environment.yml
conda activate color-number
python main.py
```

### 双击启动（macOS）

建好环境之后，在 Finder 里双击项目文件夹中的 **Color Number.app** 就能打开游戏。

- 这个 App 只是一个启动器，它会去运行同一个文件夹里的 `main.py`，所以**不要把它移出项目文件夹**。
- 想放进程序坞，可以把它拖到程序坞里（这样只会放一个快捷方式，App 本身还留在原处）。
- 启动器会在 `~/miniforge3`、`~/miniconda3`、`~/anaconda3` 等常见位置寻找 `color-number` 环境。

以后更新了 `environment.yml`，用这条命令同步：

```bash
conda env update --file environment.yml
```

## 操作方法

| 操作 | 鼠标 / 键盘 |
|---|---|
| 填色 | 左键点击或拖动 |
| 缩放 | 滚轮，或按 `+` / `-` |
| 移动画布 | 右键拖动、按住空格再拖动、"移动"工具，或方向键 |
| 撤销 | `Cmd+Z`（Windows 上是 `Ctrl+Z`） |
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
    converter.py         照片 → 填色图
    game.py              填色进度、魔棒、油漆桶、撤销、提示、回放
    storage.py           作品存档
    settings.py          设置
    library.py           内置图库（字符画）
    render.py            把进度画成图片
    export.py            导出 PNG / GIF / MP4
    audio.py             合成音效和背景音乐
    i18n.py              中英文界面文字
  ui/                    Kivy 界面
    app.py               管理各个页面
    paint_canvas.py      可以缩放的填色画布
    game_screen.py       填色页面
    home_screen.py       首页：图库和作品集
    import_screen.py     导入照片页面
    settings_screen.py   设置页面
    common.py            按钮、弹窗、字体等公共部分
    sound.py / confetti.py / exporting.py
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
- 中文字体：改用 iOS 系统字体的路径
- 导出 MP4：iPhone 上没有 ffmpeg，需要换一种方式
- 布局：适配竖屏和小屏幕

## 许可证

还没有决定。
