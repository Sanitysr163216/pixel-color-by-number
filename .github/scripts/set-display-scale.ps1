# 把 GitHub 的 Windows 电脑改成 1920×1080、屏幕缩放 <Scale>%（默认 150%），
# 用来测试游戏在高分辨率屏幕上的窗口大小和显示。
# 用的是 Windows"设置 → 显示"页面同样的接口，不需要重新登录。
param([int]$Scale = 150)

Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class Display {
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Ansi)]
    public struct DEVMODE {
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)] public string dmDeviceName;
        public short dmSpecVersion, dmDriverVersion, dmSize, dmDriverExtra;
        public int dmFields, dmPositionX, dmPositionY, dmDisplayOrientation, dmDisplayFixedOutput;
        public short dmColor, dmDuplex, dmYResolution, dmTTOption, dmCollate;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)] public string dmFormName;
        public short dmLogPixels;
        public int dmBitsPerPel, dmPelsWidth, dmPelsHeight, dmDisplayFlags, dmDisplayFrequency;
        public int dmICMMethod, dmICMIntent, dmMediaType, dmDitherType, dmReserved1, dmReserved2;
        public int dmPanningWidth, dmPanningHeight;
    }
    [StructLayout(LayoutKind.Sequential)] public struct POINT { public int X, Y; }
    [DllImport("user32.dll")] public static extern bool EnumDisplaySettings(string name, int mode, ref DEVMODE dm);
    [DllImport("user32.dll")] public static extern int ChangeDisplaySettings(ref DEVMODE dm, int flags);
    [DllImport("user32.dll")] public static extern bool SystemParametersInfo(uint action, int param, IntPtr p, uint ini);
    [DllImport("user32.dll")] public static extern IntPtr SetThreadDpiAwarenessContext(IntPtr context);
    [DllImport("user32.dll")] public static extern IntPtr MonitorFromPoint(POINT pt, uint flags);
    [DllImport("shcore.dll")] public static extern int GetDpiForMonitor(IntPtr monitor, int type, out uint x, out uint y);

    public static uint MonitorDpi() {
        SetThreadDpiAwarenessContext(new IntPtr(-4));     // 按"每个显示器"读取真正的缩放
        uint x, y;
        GetDpiForMonitor(MonitorFromPoint(new POINT(), 1), 0, out x, out y);
        return x;
    }
}
"@

# 1. 分辨率改成 1920×1080
$mode = New-Object Display+DEVMODE
$mode.dmSize = [System.Runtime.InteropServices.Marshal]::SizeOf($mode)
[void][Display]::EnumDisplaySettings($null, -1, [ref]$mode)
$mode.dmPelsWidth = 1920
$mode.dmPelsHeight = 1080
$mode.dmFields = 0x80000 -bor 0x100000
$result = [Display]::ChangeDisplaySettings([ref]$mode, 0)
Write-Output "Resolution change result: $result (0 = OK)"

# 2. 屏幕缩放：这个接口用"比推荐值高几档"来设置（每档 25%），所以设好以后量一下，不对就再调
$steps = @(100, 125, 150, 175, 200, 225, 250)
$want = [array]::IndexOf($steps, $Scale)
$relative = 0
for ($try = 0; $try -lt 4; $try++) {
    $now = [array]::IndexOf($steps, [int]([Display]::MonitorDpi() * 100 / 96))
    Write-Output "Display scale now: $($steps[$now])%"
    if ($now -eq $want) { break }
    $relative += $want - $now
    [void][Display]::SystemParametersInfo(0x009F, $relative, [IntPtr]::Zero, 1)   # SPI_SETLOGICALDPIOVERRIDE
    Start-Sleep -Seconds 3
}
$final = [int]([Display]::MonitorDpi() * 100 / 96)
Write-Output "Final display scale: $final%"
if ($final -ne $Scale) { throw "Could not set the display scale to $Scale%" }
