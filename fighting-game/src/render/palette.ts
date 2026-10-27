import { rgb } from './framebuffer';

/** Colours of a fighter. Each player gets a different set, like the alternate colours in arcade games. */
export interface FighterPalette {
  outline: number;
  gi: number;
  giShade: number;
  pants: number;
  pantsShade: number;
  skin: number;
  skinShade: number;
  hair: number;
  accent: number;
  staff: number;
}

export const FIGHTER_PALETTES: [FighterPalette, FighterPalette] = [
  {
    outline: rgb('#1a1020'),
    gi: rgb('#f2eee2'),
    giShade: rgb('#b9b2a2'),
    pants: rgb('#e8e2d2'),
    pantsShade: rgb('#a9a090'),
    skin: rgb('#efae84'),
    skinShade: rgb('#bf7850'),
    hair: rgb('#2a1a14'),
    accent: rgb('#d42a2a'),
    staff: rgb('#8a5a2a'),
  },
  {
    outline: rgb('#10101e'),
    gi: rgb('#3a64d8'),
    giShade: rgb('#26408f'),
    pants: rgb('#2f55c0'),
    pantsShade: rgb('#203a84'),
    skin: rgb('#e9a77c'),
    skinShade: rgb('#b46e48'),
    hair: rgb('#4a2a12'),
    accent: rgb('#f2c22a'),
    staff: rgb('#6a4a2a'),
  },
];

export const UI = {
  white: rgb('#ffffff'),
  text: rgb('#f4f0e6'),
  dim: rgb('#a9a3b8'),
  shadow: rgb('#000000'),
  yellow: rgb('#f8d830'),
  yellowLight: rgb('#fff3a0'),
  yellowDark: rgb('#c08a10'),
  red: rgb('#e83020'),
  barBack: rgb('#3a1418'),
  barFrame: rgb('#120a10'),
  barEdge: rgb('#d8d0c0'),
  meter: rgb('#2ea8f4'),
  meterLight: rgb('#a8e4ff'),
  meterDark: rgb('#1460a8'),
  meterBack: rgb('#0c1830'),
  hurt: rgb('#3aa0ff', 0.28),
  hurtLine: rgb('#5ab8ff'),
  hit: rgb('#ff2a2a', 0.38),
  hitLine: rgb('#ff5a4a'),
  spent: rgb('#ff9a2a', 0.2),
  spentLine: rgb('#ffb04a'),
  push: rgb('#ffe066'),
  panel: rgb('#000000', 0.45),
};
