#!/bin/bash
# 把游戏打包成 macOS App，并压缩成可以上传到 GitHub Releases 的 zip。
#
# 用法（在项目文件夹里）：
#     conda activate color-number
#     packaging/build_macos.sh
#
# 版本号从 colornumber/__init__.py 里读取（发布新版本时先改那里）。
# 结果在 dist/ 文件夹：Color Number.app 和 Color-Number-<版本>-macOS-<芯片>.zip

set -euo pipefail
cd "$(dirname "$0")/.."

VERSION="$(python -c 'import colornumber; print(colornumber.__version__)')"
if [ -n "${1:-}" ] && [ "$1" != "$VERSION" ]; then
    echo "版本号不一致：参数是 $1，colornumber/__init__.py 里是 $VERSION。请先改 __init__.py。" >&2
    exit 1
fi
ARCH="$(uname -m)"            # arm64（Apple 芯片）或 x86_64（Intel）
export COLOR_NUMBER_VERSION="$VERSION"

rm -rf build "dist/Color Number" "dist/Color Number.app"
pyinstaller --noconfirm --clean packaging/color_number.spec

ZIP="dist/Color-Number-${VERSION}-macOS-${ARCH}.zip"
rm -f "$ZIP"
# ditto 会保留 App 里的符号链接和权限，比普通 zip 更适合打包 .app
ditto -c -k --sequesterRsrc --keepParent "dist/Color Number.app" "$ZIP"
echo "Built: $ZIP ($(du -h "$ZIP" | cut -f1))"
