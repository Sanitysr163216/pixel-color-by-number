import type { CharacterData } from '../types';
import {
  crouchHK,
  forwardMK,
  forwardMP,
  leopardH,
  leopardL,
  leopardM,
  risingPushH,
  risingPushL,
  risingPushM,
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
    '2LP': null,
    '2MP': null,
    '2HP': null,
    '2LK': null,
    '2MK': null,
    '2HK': crouchHK,
    'j.LP': null,
    'j.MP': null,
    'j.HP': null,
    'j.LK': null,
    'j.MK': null,
    'j.HK': null,
  },

  commandNormals: [
    { direction: 6, button: 'MP', move: forwardMP },
    { direction: 6, button: 'MK', move: forwardMK },
  ],

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
  ],

  chakraSpecials: [],
};
