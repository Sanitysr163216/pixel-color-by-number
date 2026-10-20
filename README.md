# Color Number

**English** | [中文](README.zh-CN.md)

A pixel-art color-by-number game for the desktop, written in Python with [Kivy](https://kivy.org).
Turn any photo into a numbered grid of cells, then paint it cell by cell.

The interface is in English by default; Chinese is available under **Settings → Language**.

## Features

- **Built-in library**: mushrooms, ginger cat, strawberry, ice cream, little house, cactus, clownfish and a lake sunset
- **Import your own photos** (JPG, PNG, iPhone HEIC, …): crop, adjust brightness/contrast/saturation, choose the grid size and number of colors, live preview, one-click reset to defaults
  - **Three styles**: **Smooth** (default: soft color transitions, rounded shapes without jagged corners), **Sharp** (sharpened edges, most detail) and **Classic** (the first version's algorithm)
  - **Compare with the original**: drag a divider between the original photo and the pixel art, with a "similar to the original" score
  - Colors are chosen in the perceptual Lab color space, and small but striking colors (eye whites, lips, highlights) get their own palette slots
  - **Recommended color count** for each picture (faithful, yet with colors that are easy to tell apart), plus a warning when colors look alike
  - **AI assist** (macOS): Apple's on-device Vision framework finds faces, facial features and the main subject, keeps more detail in faces and can blur the background
- **Painting**: click or drag to paint, brush sizes 1×1 / 3×3 / 5×5; zoom with the mouse wheel, trackpad pinch or Cmd+scroll; pan with two fingers on the trackpad. Zoomed out you see a grey outline of the picture; zoom in and it fades to white cells with numbers
- **Helpers** (unlimited): highlight the current number, magic wand (fills a connected area), bucket (fills every cell of the current number; **hold** it to fill the whole picture), hint (jumps to an unfilled cell), eyedropper (Option-click), unlimited undo that survives restarts, and redo
- **Palette**: remaining progress per color, a check mark when a color is done, auto-advance to the next color
- **When finished**: confetti and a fast replay of your painting; export as PNG, animated GIF or MP4 video
- **Gallery**: filter in-progress / finished pictures; continue, rename, restart, export or delete; progress is saved automatically
- **Music**: 8 relaxing CC0 tracks (see credits below) plus 5 synthesized tracks, shuffled; import your own music (MP3, OGG, FLAC, WAV, M4A, …) and choose which sources to play
- **Sound effects** (synthesized): fill "pops" climb a pentatonic scale as you drag; a softer sound for wrong colors
- **Settings**: language, what happens on a wrong color (block it, or paint it and mark it wrong), larger grid and color limits, sound and music volume

## Install and run

Install [Miniforge](https://github.com/conda-forge/miniforge) (conda) first, then:

```bash
conda env create --file environment.yml
conda activate color-number
python main.py
```

After pulling new changes, update the environment with:

```bash
conda env update --file environment.yml
```

### Double-click launcher (macOS)

Once the environment exists, double-click **Color Number.app** in the project folder.
It is only a launcher that runs `main.py` from the same folder, so keep it inside the project folder
(drag it to the Dock to create a shortcut). It looks for the `color-number` environment in
`~/miniforge3`, `~/miniconda3`, `~/anaconda3` and other common locations.

The game is developed and tested on macOS. Kivy also runs on Windows and Linux, but AI assist,
trackpad gestures and the native file picker are macOS-only there.

## Controls

| Action | Mouse / keyboard |
|---|---|
| Paint | Left click or drag |
| Zoom | Trackpad pinch, mouse wheel, Cmd/Ctrl + scroll, the + / − buttons, or `+` / `-` |
| Pan | Two-finger trackpad swipe, right-drag, hold Space and drag, the Move tool, or arrow keys |
| Eyedropper (select a cell's color) | Option-click (Alt-click on Windows) |
| Undo / redo | `Cmd+Z` / `Cmd+Shift+Z` (`Ctrl+Z` / `Ctrl+Y` on Windows) |
| Brush size | `[` smaller, `]` larger |
| Fill the whole picture | Hold the Bucket button |
| Hint | `H` |
| Tools | `B` brush, `W` wand, `M` move |
| Fit to window | `0` |

On touch screens: one finger paints, two fingers zoom and pan.

## Where files are stored

- Saved pictures and settings: `~/Library/Application Support/colornumber/` (macOS)
- Exports: `~/Pictures/Color Number/`

## Project layout

```
main.py                  entry point
colornumber/
  core/                  game logic in plain Python, no Kivy (reusable for a future iPhone version)
    picture.py           a color-by-number picture (palette + numbered cells)
    converter.py         photo → picture (Lab palette, styles, recommended color count)
    vision.py            AI assist with Apple Vision (macOS only)
    game.py              painting, wand, bucket, undo/redo, hints, replay
    storage.py           saving pictures and progress
    settings.py          settings
    library.py           built-in pictures
    render.py            draws progress as an image
    export.py            PNG / GIF / MP4 export
    audio.py             synthesized sound effects and music
    music.py             music library: featured tracks and imported music
    i18n.py              English and Chinese interface text
  assets/music/          featured music (OGG) and credits.json
  ui/                    Kivy interface: screens, zoomable canvas, dialogs, sound, trackpad gestures
preview.py               preview a photo conversion from the command line
tests/                   automated tests (run `pytest`)
exercises/               Python exercises that go with the project (in Chinese)
```

Code comments are written in Chinese: the project started as a way to learn Python.

## Tests

```bash
pytest
```

## Music credits

All featured tracks come from OpenGameArt's
["CC0 - Calm / Relaxing Music"](https://opengameart.org/content/cc0-calm-relaxing-music) collection and are
released under CC0 (public domain). They were converted to loudness-matched OGG files. Thank you to the artists:

| Track | Artist | Source |
|---|---|---|
| Vaporware | cynicmusic (The Cynic Project) | [link](https://opengameart.org/content/calm-piano-1-vaporware) |
| Good Morning | Cakeflaps @ You're Perfect Studio | [link](https://opengameart.org/content/good-morning) |
| Another August | cynicmusic (The Cynic Project) | [link](https://opengameart.org/content/another-august) |
| November Snow | cynicmusic (The Cynic Project) | [link](https://opengameart.org/content/november-snow) |
| Serenade | Pro Sensory (Alex McCulloch) | [link](https://opengameart.org/content/serenade-guitar) |
| Bossa Shop Theme | SpringySpringo | [link](https://opengameart.org/content/bossa-shop-theme-in-low-fi-and-hd) |
| A Simple Trifle | jestar | [link](https://opengameart.org/content/a-simple-trifle) |
| Menu Chill | etrock | [link](https://opengameart.org/content/menu-chill-music) |

## License

The code is released under the [MIT License](LICENSE). The featured music in `colornumber/assets/music/`
is CC0 (public domain); see the credits above.
