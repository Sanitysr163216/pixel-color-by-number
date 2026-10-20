"""
Mac 触控板手势：双指捏合缩放，双指滑动移动画布。

Kivy 在 Mac 上收不到触控板的手势，所以这里用 pyobjc 直接监听 macOS 的事件：
- 捏合是"放大"（magnify）事件，带着这次缩放了多少
- 触控板双指滑动是"精确滚动"事件（hasPreciseScrollingDeltas 为真），
  普通鼠标滚轮不是。所以触控板滑动用来移动画布，鼠标滚轮仍然用来缩放。
- 苹果的 Magic Mouse 滚动也是"精确滚动"，但它没有捏合手势，
  所以按住 Cmd 或 Ctrl 再滚动（触控板也一样）就是缩放。

只有鼠标在画布上时才处理；其他时候把事件原样交还给 Kivy（比如首页的列表照常滚动）。
"""

import math
import sys

try:
    import AppKit
    _AVAILABLE = sys.platform == "darwin"
except ImportError:
    _AVAILABLE = False

_monitor = None   # 保存监听器，避免被当成垃圾回收


def available():
    return _AVAILABLE


def handle_event(event, get_target):
    """
    处理一个 macOS 事件。返回 None 表示事件已经用掉（Kivy 不会再收到），
    否则原样返回事件。单独写成函数，方便测试。
    """
    target = get_target()
    if target is None:
        return event
    event_type = event.type()
    if event_type == AppKit.NSEventTypeMagnify:
        target.gesture_zoom(1.0 + event.magnification())
        return None
    if event_type == AppKit.NSEventTypeScrollWheel and event.hasPreciseScrollingDeltas():
        zoom_keys = AppKit.NSEventModifierFlagCommand | AppKit.NSEventModifierFlagControl
        if event.modifierFlags() & zoom_keys:
            amount = event.scrollingDeltaY()
            if event.isDirectionInvertedFromDevice():     # "自然滚动"打开时方向是反的
                amount = -amount
            target.gesture_zoom(math.exp(max(-0.5, min(0.5, amount * 0.012))))
            return None
        window = event.window()
        scale = window.backingScaleFactor() if window is not None else 2.0   # 视网膜屏 1 点 = 2 像素
        target.gesture_pan(event.scrollingDeltaX() * scale, -event.scrollingDeltaY() * scale)
        return None
    return event


def install(get_target):
    """
    开始监听触控板手势。get_target() 返回现在应该接收手势的画布，没有就返回 None。
    成功返回 True。
    """
    global _monitor
    if not _AVAILABLE or _monitor is not None:
        return False
    mask = AppKit.NSEventMaskMagnify | AppKit.NSEventMaskScrollWheel
    _monitor = AppKit.NSEvent.addLocalMonitorForEventsMatchingMask_handler_(
        mask, lambda event: handle_event(event, get_target))
    return _monitor is not None
