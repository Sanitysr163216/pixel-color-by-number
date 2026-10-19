"""
检查你在 exercises/progress.py 里写的函数。

运行方法：在 VS Code 里选择 color-number 环境，然后运行这个文件。
每个测试会显示 [OK] 或 [FAIL]。
"""

from progress import count_cells


def check(description, actual, expected):
    """比较实际结果和预期结果，打印 [OK] 或 [FAIL]。返回是否通过。"""
    if actual == expected:
        print(f"[OK]   {description}")
        return True
    print(f"[FAIL] {description}")
    print(f"       预期 {expected!r}，实际得到 {actual!r}")
    return False


def check_exercise_1():
    print("练习 1：count_cells")
    small = [
        [1, 1, 2],
        [2, 1, 2],
    ]
    results = [
        check("数 1 号：应该是 3 格", count_cells(small, 1), 3),
        check("数 2 号：应该是 3 格", count_cells(small, 2), 3),
        check("数不存在的 5 号：应该是 0 格", count_cells(small, 5), 0),
        check("只有一格的图", count_cells([[7]], 7), 1),
        check("一行很长的图", count_cells([[3, 3, 3, 3, 1, 3]], 3), 5),
        check("一列很高的图", count_cells([[4], [4], [2], [4]], 4), 3),
    ]
    return all(results)


if __name__ == "__main__":
    if check_exercise_1():
        print("\n练习 1 全部通过！🎉")
    else:
        print("\n还有没通过的，再看看提示。")
