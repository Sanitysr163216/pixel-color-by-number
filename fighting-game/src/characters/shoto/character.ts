import type { CharacterData } from '../types';
import {
  crouchHK,
  crouchHP,
  crouchLK,
  crouchLP,
  crouchMK,
  crouchMP,
  jumpHK,
  jumpHP,
  jumpLK,
  jumpLP,
  jumpMK,
  jumpMP,
  soulFlakeCE,
  soulFlakeH,
  soulFlakeL,
  soulFlakeM,
  spiritualTunneling,
  forwardMK,
  forwardMP,
  leopardH,
  leopardL,
  leopardM,
  risingPushH,
  risingPushL,
  risingPushM,
  shoulderThrow,
  standHK,
  standLP,
  standMP,
} from './moves';

/** Character 1: Shoto / "zoner". null = not made yet (the button is read, nothing happens). */
export const shoto: CharacterData = {
  name: 'Shoto',
  health: 1000,
  walkForward: 2.5,
  walkBack: 2,
  jump: { squat: 4, up: 10, forward: 3, back: 2.5 },
  // Like Bishamon in Vampire Savior, scaled to this character's size: a fast continuous dash forward,
  // a short hop backward.
  dash: { speed: 5 },
  backHop: { up: 4.5, back: 3.5 },

  hurtboxes: {
    stand: [
      { x: -6, y: 76, w: 18, h: 20 }, // head
      { x: -14, y: 40, w: 30, h: 36 }, // body
      { x: -16, y: 0, w: 34, h: 40 }, // legs
    ],
    crouch: [
      { x: -2, y: 46, w: 18, h: 16 },
      { x: -16, y: 0, w: 36, h: 46 },
    ],
    air: [
      { x: -6, y: 70, w: 18, h: 18 },
      { x: -14, y: 22, w: 30, h: 48 },
    ],
  },
  pushboxes: {
    stand: { x: -16, y: 0, w: 32, h: 80 },
    crouch: { x: -18, y: 0, w: 36, h: 56 },
    air: { x: -14, y: 16, w: 28, h: 60 },
    down: { x: -26, y: 0, w: 52, h: 14 },
  },

  normals: {
    '5LP': standLP,
    '5MP': standMP,
    '5HP': null,
    '5LK': null,
    '5MK': null,
    '5HK': standHK,
    '2LP': crouchLP,
    '2MP': crouchMP,
    '2HP': crouchHP,
    '2LK': crouchLK,
    '2MK': crouchMK,
    '2HK': crouchHK,
    'j.LP': jumpLP,
    'j.MP': jumpMP,
    'j.HP': jumpHP,
    'j.LK': jumpLK,
    'j.MK': jumpMK,
    'j.HK': jumpHK,
  },

  commandNormals: [
    { direction: 6, button: 'MP', move: forwardMP },
    { direction: 6, button: 'MK', move: forwardMK },
  ],

  throw: { range: 52, direction: 6, buttons: ['MP', 'HP'], move: shoulderThrow },

  specials: [
    {
      id: 'leopard',
      name: 'Leopard Strike',
      motion: [4, 2, 1, 6],
      window: 20,
      button: 'P',
      L: leopardL,
      M: leopardM,
      H: leopardH,
      CE: null,
    },
    {
      id: 'rising',
      name: 'Rising Push',
      motion: [6, 2, 3],
      window: 15,
      button: 'K',
      L: risingPushL,
      M: risingPushM,
      H: risingPushH,
      CE: null,
    },
    {
      // After Leopard Strike in this list: a rolled 4-2-1-6 also passes through 2-3-6, and Leopard should win.
      id: 'flake',
      name: 'Soul Flake',
      motion: [2, 3, 6],
      window: 12,
      button: 'P',
      L: soulFlakeL,
      M: soulFlakeM,
      H: soulFlakeH,
      CE: soulFlakeCE,
    },
  ],

  chakraSpecials: [
    {
      id: 'tunneling',
      name: 'Spiritual Tunneling',
      motion: [4, 1, 2, 3, 6],
      window: 24,
      button: 'P',
      buttons: 2,
      move: spiritualTunneling,
    },
  ],
};
