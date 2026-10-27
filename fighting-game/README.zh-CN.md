# 格斗游戏原型

[English](README.md) | **中文**

一个在浏览器里运行的 6 键 2D 格斗游戏，画风参考 KOF97。这一版有角色 1（Shoto）的全部已定义招式、
训练模式和双人对战模式。正式美术完成之前，角色先用占位的像素小人。

规则、帧数的算法和现在的帧数表在 [docs/design.md](docs/design.md)（英文，方便你朋友看）。

## 运行

需要 [Node.js](https://nodejs.org) 20 或更新版本。

```sh
cd fighting-game
npm install
npm run dev        # 给出一个本地网址，打开就能玩；改了文件会自动刷新
npm test           # 70 个逐帧测试，检查所有规则
npm run build      # 在 dist/ 生成正式版，可以放到任何网页空间
```

## 操作

| | 玩家 1 | 玩家 2（对战模式） |
| --- | --- | --- |
| 移动 / 跳 / 蹲 | W A S D | 方向键 |
| LP MP HP（轻中重拳） | U I O | 小键盘 4 5 6 |
| LK MK HK（轻中重脚） | J K L | 小键盘 1 2 3 |
| 手柄 | 第一个手柄：X Y RB = 拳，A B RT = 脚 | 第二个手柄 |

按住后方向防御，按住后下方向防下段。

训练模式按键：`1` 判定框，`2` 帧数信息，`3` 暂停，`4` 暂停时前进一帧，`5` 陪练站 / 蹲 / 跳，
`6` 陪练防御，`7` 训练 / 对战切换，`8` 能量全满，`0` 回到起始位置。

两个人共用一个键盘会有按键冲突，对战时建议至少一人用手柄。

## 修改招式

每个招式是 `src/characters/shoto/moves.ts` 里的一段数字，例如：

```ts
export const standLP: MoveData = {
  name: 'Palm Strike',
  kind: 'normal',
  strength: 'L',
  startup: 4,          // 第 1–4 帧没有判定，第 5 帧出 hitbox
  active: 2,           // hitbox 持续 2 帧
  recovery: 7,         // 之后 7 帧不能行动
  damage: 30,
  hitstun: 12,
  blockstun: 8,
  knockback: { distance: 14, speed: 3.5 },   // 击退距离（像素）和速度（像素/帧）
  hitboxes: [{ boxes: [{ x: 24, y: 70, w: 22, h: 14 }] }],
  hurtboxes: [{ frames: [5, 9], boxes: [{ x: 10, y: 72, w: 26, h: 10 }] }],
};
```

每个字段的说明在 `src/moves/types.ts`。数字写错（比如 hitbox 超出了 active 帧）时，游戏会停下并说明是哪个招式出错。
改完运行 `npm test`：测试检查的是规则而不是具体数值，所以调数值不会让测试失败。

## 结构

- **TypeScript**，不用游戏引擎。对战逻辑（`src/sim/`）一次严格前进一帧，坐标都是整数，同样的输入永远得到同样的结果，
  所以测试可以精确到帧，以后也能做录像回放和联机。
- **招式是数据**（`src/characters/`），启动时检查（`src/moves/compile.ts`）。
- **画面**（`src/render/`）逐像素画在 304×224 的画面上（KOF97 的画面大小），再放大，像素边缘清晰。
- **Vite** 负责打包网页，**Vitest** 负责测试。
