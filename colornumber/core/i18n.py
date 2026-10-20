"""
界面文字的中英文翻译。

用法：tr("undo", "zh") → "撤销"；tr("undo", "en") → "Undo"。
文字里可以有 {占位符}，用关键字参数填进去：
tr("percent_done", "zh", percent=40) → "已完成 40%"
"""

LANGUAGES = ("zh", "en")

STRINGS = {
    # 通用
    "app_title": {"zh": "Color Number 数字填色", "en": "Color Number"},
    "ok": {"zh": "确定", "en": "OK"},
    "cancel": {"zh": "取消", "en": "Cancel"},
    "back": {"zh": "返回", "en": "Back"},
    "close": {"zh": "关闭", "en": "Close"},
    "delete": {"zh": "删除", "en": "Delete"},
    "continue": {"zh": "继续", "en": "Continue"},

    # 首页
    "library": {"zh": "图库", "en": "Library"},
    "my_works": {"zh": "我的作品", "en": "My Works"},
    "import_photo": {"zh": "导入照片", "en": "Import Photo"},
    "settings": {"zh": "设置", "en": "Settings"},
    "filter_all": {"zh": "全部", "en": "All"},
    "filter_in_progress": {"zh": "进行中", "en": "In Progress"},
    "filter_completed": {"zh": "已完成", "en": "Completed"},
    "no_works": {"zh": "还没有作品。从图库挑一张，或者导入一张照片吧！",
                 "en": "No works yet. Pick one from the library or import a photo!"},
    "percent_done": {"zh": "已完成 {percent}%", "en": "{percent}% done"},
    "completed": {"zh": "已完成", "en": "Completed"},
    "not_started": {"zh": "未开始", "en": "Not started"},
    "restart": {"zh": "重新开始", "en": "Restart"},
    "rename": {"zh": "重命名", "en": "Rename"},
    "export": {"zh": "导出", "en": "Export"},
    "confirm_restart": {"zh": "确定要清空「{name}」的进度、从头开始吗？",
                        "en": "Clear all progress of \"{name}\" and start over?"},
    "confirm_delete": {"zh": "确定要删除「{name}」吗？删除后无法恢复。",
                       "en": "Delete \"{name}\"? This cannot be undone."},
    "drop_hint": {"zh": "也可以把照片直接拖进窗口", "en": "You can also drag a photo into the window"},

    # 图库里图片的名字
    "library_mushroom": {"zh": "蘑菇", "en": "Mushroom"},
    "library_cat": {"zh": "橘猫", "en": "Ginger Cat"},
    "library_strawberry": {"zh": "草莓", "en": "Strawberry"},
    "library_ice_cream": {"zh": "冰淇淋", "en": "Ice Cream"},
    "library_house": {"zh": "小房子", "en": "Little House"},
    "library_cactus": {"zh": "仙人掌", "en": "Cactus"},
    "library_fish": {"zh": "小丑鱼", "en": "Clownfish"},
    "library_sunset": {"zh": "湖边日落", "en": "Lake Sunset"},

    # 填色页面
    "undo": {"zh": "撤销", "en": "Undo"},
    "redo": {"zh": "重做", "en": "Redo"},
    "brush_size": {"zh": "笔刷大小", "en": "Brush size"},
    "hint": {"zh": "提示", "en": "Hint"},
    "finished_menu": {"zh": "导出…", "en": "Export…"},
    "tool_brush": {"zh": "画笔", "en": "Brush"},
    "tool_wand": {"zh": "魔棒", "en": "Wand"},
    "tool_bucket": {"zh": "油漆桶", "en": "Bucket"},
    "bucket_hint": {"zh": "长按：填完整张图", "en": "Hold: fill everything"},
    "fill_all": {"zh": "一键填完", "en": "Fill All"},
    "confirm_fill_all": {"zh": "要一键填完剩下的 {cells} 格吗？填完后可以撤销。",
                         "en": "Fill the remaining {cells} cells at once? You can undo it afterwards."},
    "tool_move": {"zh": "移动", "en": "Move"},
    "fit_view": {"zh": "全图", "en": "Fit"},
    "progress": {"zh": "{percent}%", "en": "{percent}%"},
    "controls_help": {
        "zh": "捏合/滚轮 缩放\nCmd+滚动 缩放\n双指滑 移动\n右键拖 移动\nOption+点 吸色\nCmd+Z 撤销\n[ ] 笔刷大小\nH 提示",
        "en": "Pinch: zoom\nWheel: zoom\nCmd+wheel: zoom\n2 fingers: pan\nRight-drag: pan\nOpt+click: pick\nCmd+Z: undo\n[ ]: brush\nH: hint",
    },
    "picture_complete": {"zh": "完成啦！", "en": "Finished!"},
    "export_png": {"zh": "导出图片 PNG", "en": "Export PNG"},
    "export_gif": {"zh": "导出动图 GIF", "en": "Export GIF"},
    "export_mp4": {"zh": "导出视频 MP4", "en": "Export MP4"},
    "back_to_gallery": {"zh": "回到作品集", "en": "Back to Gallery"},
    "keep_looking": {"zh": "继续欣赏", "en": "Keep Looking"},
    "replay": {"zh": "再看一遍", "en": "Replay"},
    "exporting": {"zh": "正在导出……", "en": "Exporting…"},
    "exported_to": {"zh": "已保存到：\n{path}", "en": "Saved to:\n{path}"},
    "show_in_finder": {"zh": "在 Finder 中显示", "en": "Show in Finder"},
    "export_failed": {"zh": "导出失败：{error}", "en": "Export failed: {error}"},

    # 导入页面
    "choose_photo": {"zh": "选择照片", "en": "Choose Photo"},
    "crop_hint": {"zh": "拖动方框裁剪，拖动四角调整大小",
                  "en": "Drag the box to crop, drag its corners to resize"},
    "reset_crop": {"zh": "不裁剪", "en": "Full Image"},
    "grid_size": {"zh": "格子数（长边）", "en": "Grid size"},
    "color_count": {"zh": "颜色数", "en": "Colors"},
    "brightness": {"zh": "亮度", "en": "Brightness"},
    "contrast": {"zh": "对比度", "en": "Contrast"},
    "saturation": {"zh": "饱和度", "en": "Saturation"},
    "clean_stray": {"zh": "清理杂色点", "en": "Remove specks"},
    "detail": {"zh": "细节", "en": "Detail"},
    "smoothness": {"zh": "平滑度", "en": "Smoothness"},
    "style_smooth": {"zh": "平滑", "en": "Smooth"},
    "style_clear": {"zh": "清晰", "en": "Sharp"},
    "style_classic": {"zh": "经典", "en": "Classic"},
    "compare_original": {"zh": "对比原图", "en": "Compare"},
    "original_label": {"zh": "原图", "en": "Original"},
    "pixel_label": {"zh": "填色图", "en": "Pixel art"},
    "reset_defaults": {"zh": "恢复默认", "en": "Defaults"},
    "fidelity": {"zh": "· 与原图相似 {score}%", "en": "· {score}% like the original"},
    "fidelity_adjusted": {"zh": "（含你的调整）", "en": " (incl. your edits)"},
    "creating_picture": {"zh": "正在生成填色图……", "en": "Creating your picture…"},
    "use_recommended": {"zh": "使用推荐", "en": "Use it"},
    "recommend_working": {"zh": "正在计算推荐的颜色数……", "en": "Finding a good color count…"},
    "recommended_colors": {"zh": "推荐 {count} 种颜色：能还原这张图，颜色之间也好区分",
                           "en": "Recommended: {count} colors (faithful and easy to tell apart)"},
    "similar_warning": {"zh": "· 其中 {pairs} 对颜色很接近", "en": "· {pairs} pairs of colors look alike"},
    "ai_assist": {"zh": "AI 识别", "en": "AI assist"},
    "blur_background": {"zh": "虚化背景", "en": "Blur background"},
    "ai_analyzing": {"zh": "AI 正在识别人脸和主体……", "en": "AI is looking for faces and the subject…"},
    "ai_failed": {"zh": "AI 识别没有成功，照常转换", "en": "AI analysis failed; converting normally"},
    "ai_found_faces_subject": {"zh": "AI：找到 {faces} 张人脸和主体，五官会保留更多细节",
                               "en": "AI: found {faces} face(s) and the subject; facial features keep more detail"},
    "ai_found_faces": {"zh": "AI：找到 {faces} 张人脸，五官会保留更多细节",
                       "en": "AI: found {faces} face(s); facial features keep more detail"},
    "ai_found_subject": {"zh": "AI：找到主体，可以虚化背景", "en": "AI: found the subject; you can blur the background"},
    "ai_classic_note": {"zh": "AI：找到 {faces} 张人脸（经典模式不加强五官细节，只能用来虚化背景）",
                        "en": "AI: found {faces} face(s) (Classic mode doesn't sharpen faces; only background blur applies)"},
    "ai_found_nothing": {"zh": "AI：没有找到人脸或明显的主体", "en": "AI: no face or clear subject found"},
    "name": {"zh": "名字", "en": "Name"},
    "start_coloring": {"zh": "开始填色", "en": "Start Coloring"},
    "preview_info": {"zh": "{width} × {height} 格 · {colors} 种颜色",
                     "en": "{width} × {height} cells · {colors} colors"},
    "load_failed": {"zh": "无法打开这张图片：{error}", "en": "Could not open this image: {error}"},
    "pick_photo_title": {"zh": "选择一张照片", "en": "Choose a photo"},

    # 设置页面
    "language": {"zh": "语言", "en": "Language"},
    "wrong_mode": {"zh": "颜色填错时", "en": "When the color is wrong"},
    "wrong_block": {"zh": "不让填", "en": "Don't paint"},
    "wrong_allow": {"zh": "填上但标为错误", "en": "Paint, mark as wrong"},
    "grid_limit": {"zh": "格子上限（长边）", "en": "Max grid size (long side)"},
    "color_limit": {"zh": "颜色上限", "en": "Max colors"},
    "sound": {"zh": "音效", "en": "Sound effects"},
    "music": {"zh": "背景音乐", "en": "Background music"},
    "sound_volume": {"zh": "音效音量", "en": "Sound volume"},
    "music_volume": {"zh": "音乐音量", "en": "Music volume"},
    "now_playing": {"zh": "正在播放：{track}", "en": "Now playing: {track}"},
    "nothing_playing": {"zh": "音乐准备中……", "en": "Preparing music…"},
    "music_is_off": {"zh": "背景音乐已关闭", "en": "Background music is off"},
    "no_my_music": {"zh": "\"我的音乐\"里还没有歌，先导入几首吧", "en": "No songs in My music yet. Import some first."},
    "next_track": {"zh": "下一首", "en": "Next"},
    "music_source": {"zh": "曲库", "en": "Play from"},
    "source_all": {"zh": "全部", "en": "All"},
    "source_featured": {"zh": "精选", "en": "Featured"},
    "source_synth": {"zh": "合成", "en": "Synth"},
    "source_mine": {"zh": "我的音乐", "en": "My music"},
    "my_music": {"zh": "我的音乐", "en": "My music"},
    "import_music": {"zh": "导入音乐", "en": "Import Music"},
    "my_music_count": {"zh": "已导入 {count} 首（支持 MP3、OGG、FLAC、WAV、M4A 等）",
                       "en": "{count} imported (MP3, OGG, FLAC, WAV, M4A …)"},
    "importing_music": {"zh": "正在导入……", "en": "Importing…"},
    "import_music_failed": {"zh": "这些文件没能导入：\n{files}", "en": "Could not import:\n{files}"},
    "confirm_delete_music": {"zh": "确定要删除「{name}」吗？", "en": "Delete \"{name}\"?"},
    "pick_music_title": {"zh": "选择音乐（可以多选）", "en": "Choose music (you can pick several)"},
    "music_music_box": {"zh": "音乐盒的早晨", "en": "Music Box Morning"},
    "music_rainy": {"zh": "雨天的窗边", "en": "Rainy Window"},
    "music_garden": {"zh": "花园散步", "en": "Garden Stroll"},
    "music_starry": {"zh": "星空", "en": "Starry Night"},
    "music_sunday": {"zh": "慵懒的周日", "en": "Lazy Sunday"},
    "on": {"zh": "开", "en": "On"},
    "off": {"zh": "关", "en": "Off"},
    "warning": {"zh": "注意", "en": "Warning"},
    "grid_warning": {
        "zh": "格子长边超过 128 时，图片会非常大（{value} × {value} 约 {cells_wan} 万格），"
              "填色、缩放和保存都可能卡顿。确定要开启吗？",
        "en": "Above 128 cells the picture gets very large ({value} × {value} ≈ {cells_k}k cells). "
              "Painting, zooming and saving may lag. Enable anyway?",
    },
    "color_warning": {
        "zh": "颜色超过 36 种时，相近的颜色会很难分辨，图也更难填完。确定要开启吗？",
        "en": "With more than 36 colors, similar colors become hard to tell apart. Enable anyway?",
    },
}


def tr(key, language, **values):
    """取出 key 对应的文字；找不到翻译时退回中文，再找不到就显示 key 本身。"""
    entry = STRINGS.get(key)
    if entry is None:
        return key
    text = entry.get(language) or entry["zh"]
    return text.format(**values) if values else text


def project_name(meta, language):
    """
    作品显示的名字。内置图的作品如果还是默认名字（任何一种语言的），
    就按当前语言显示；玩家自己改过的名字原样显示。
    """
    source = meta.get("source", "")
    if source.startswith("library:"):
        key = "library_" + source.split(":", 1)[1]
        if key in STRINGS and meta["name"] in STRINGS[key].values():
            return tr(key, language)
    return meta["name"]
