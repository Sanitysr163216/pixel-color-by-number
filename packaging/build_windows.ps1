# 把游戏打包成 Windows 程序，并压缩成可以上传到 GitHub Releases 的 zip。
# 只能在 Windows 上运行（PyInstaller 不能在 Mac 上打包 Windows 程序）。
#
# 用法（在项目文件夹里，用 PowerShell）：
#     pip install -r packaging/requirements-windows.txt     # 只需要装一次
#     packaging/build_windows.ps1
#
# 版本号从 colornumber/__init__.py 里读取。
# 结果在 dist 文件夹：Color Number\Color Number.exe 和 Color-Number-<版本>-Windows-x64.zip

$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

$version = python -c "import colornumber; print(colornumber.__version__)"
if ($LASTEXITCODE -ne 0) { throw "Python not found" }

Remove-Item -Recurse -Force "build", "dist/Color Number" -ErrorAction SilentlyContinue
pyinstaller --noconfirm --clean packaging/color_number_windows.spec
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed" }

$zip = "dist/Color-Number-$version-Windows-x64.zip"
Remove-Item -Force $zip -ErrorAction SilentlyContinue
Compress-Archive -Path "dist/Color Number" -DestinationPath $zip
$size = [math]::Round((Get-Item $zip).Length / 1MB)
Write-Output "Built: $zip ($size MB)"
