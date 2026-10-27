# Color Number

**English** | [中文](README.zh-CN.md)

A pixel-art color-by-number game for the desktop, written in Python with [Kivy](https://kivy.org).
Turn any photo into a numbered grid of cells, then paint it cell by cell.

The interface is in English by default; Chinese is available under **Settings → Language**.

## Features

- **Built-in library**: 24 pictures in four categories (animals, food, nature, things), from a ginger cat and a penguin to a donut, a starry lake and a lighthouse
- **Art**: 27 built-in masterpieces, Chinese and Western, that work **offline** (also in mainland China), from The Met (CC0) and the National Palace Museum, Taipei (CC BY 4.0), with full credits; plus online search of public-domain paintings and prints from the [Art Institute of Chicago](https://www.artic.edu) (CC0)
- **Import your own photos** (JPG, PNG, iPhone HEIC, …): crop, adjust brightness/contrast/saturation, choose the grid size and number of colors (drag the sliders or type a number), live preview that you can zoom and pan, one-click reset to defaults
  - **Three styles**: **Smooth** (default: soft color transitions, rounded shapes without jagged corners), **Sharp** (sharpened edges, most detail) and **Classic** (the first version's algorithm)
  - **Compare with the original**: drag a divider between the original photo and the pixel art, with a "similar to the original" score
  - Colors are chosen in the perceptual Lab color space, and small but striking colors (eye whites, lips, highlights) get their own palette slots
  - **Recommended color count** for each picture (faithful, yet with colors that are easy to tell apart), plus a warning when colors look alike
  - **AI assist** (macOS): Apple's on-device Vision framework finds faces, facial features and the main subject, keeps more detail in faces and can blur the background
- **Painting**: a toolbar with icons (tools, brush size, fill, view) and a **Shortcuts** list; click or drag to paint, brush sizes 1×1 / 3×3 / 5×5; zoom with the mouse wheel, trackpad pinch or Cmd+scroll; pan with two fingers on the trackpad. Zoomed out you see a grey outline of the picture; zoom in and it fades to white cells with numbers
- **Helpers** (unlimited): highlight the current number, magic wand (fills a connected area), bucket (fills every cell of the current number; **hold** it to fill the whole picture), hint (jumps to an unfilled cell), eyedropper (Option-click), unlimited undo and redo that survive restarts (the buttons dim when there is nothing to undo or redo)
- **Palette**: remaining progress per color, a check mark when a color is done, auto-advance to the next color
- **When finished**: confetti and a fast replay of your painting; export as PNG, animated GIF or MP4 video
- **Gallery**: filter in-progress / finished pictures; continue, rename, restart, export or delete; progress is saved automatically
- **Hide pictures** you don't want to see, in the Library or My Works (from the card's … menu). They are not deleted: **Show hidden** brings them back
- **Music**: 8 relaxing CC0 tracks (see credits below) plus 5 synthesized tracks, shuffled; pick any track from the list in Settings; import your own music (MP3, OGG, FLAC, WAV, M4A, …) and choose which sources to play
- **Sound effects** (synthesized): fill "pops" climb a pentatonic scale as you drag; a softer sound for wrong colors
- **Settings**: language, what happens on a wrong color (block it, or paint it and mark it wrong), larger grid and color limits, sound and music volume

## Play on your phone (iPhone and Android)

Open **https://sanitysr163216.github.io/pixel-color-by-number/** on your phone and add it to the home screen:

- **iPhone / iPad**: in Safari, tap the Share button, then **Add to Home Screen**.
- **Android**: in Chrome, open the menu and tap **Install app** (or **Add to Home screen**).

It then opens like an app, works offline and keeps your progress on the phone. It is free and never expires.
The phone version has the built-in library, painting with touch (one finger paints, two fingers zoom and pan),
undo/redo, wand, bucket, hints, hiding pictures, and photo import with the same converter as the desktop app
(the converter, about 17 MB, is downloaded the first time you import a photo). Finished pictures can be saved
as PNG through the share sheet.

## Download and play

The easiest way on a computer: download the ready-made app, no Python needed.

### macOS

1. Open the [latest release](https://github.com/Sanitysr163216/pixel-color-by-number/releases/latest)
   and download `Color-Number-<version>-macOS-arm64.zip`.
   It runs on Macs with Apple silicon (M1 or newer) and macOS 12 or later.
2. Double-click the zip to unpack it, then drag **Color Number.app** into your **Applications** folder.
3. Open it. The first time, macOS says it cannot verify the developer, because the app is not signed
   with a paid Apple Developer ID. To allow it:
   - Click **Done** (or **OK**) in that message.
   - Open **System Settings → Privacy & Security**, scroll down and click **Open Anyway** next to
     "Color Number", then confirm with your password or Touch ID.
   - From then on it opens normally.

The downloadable app can export PNG and GIF. MP4 export needs [ffmpeg](https://ffmpeg.org);
if you install it with Homebrew (`brew install ffmpeg`), the MP4 button appears automatically.

### Windows

1. Open the [latest release](https://github.com/Sanitysr163216/pixel-color-by-number/releases/latest)
   and download `Color-Number-<version>-Windows-x64.zip`. It runs on 64-bit Windows 10 and 11.
2. Right-click the zip → **Extract All…**, and choose where to put the **Color Number** folder.
3. Open the folder and double-click **Color Number.exe**. The first time, Windows SmartScreen may say
   "Windows protected your PC", because the app is not signed with a paid certificate.
   Click **More info → Run anyway**. From then on it opens normally.
   Tip: right-click **Color Number.exe → Show more options → Send to → Desktop (create shortcut)**.

The Windows app can export PNG and GIF, and import music in MP3, OGG, FLAC and WAV.
For MP4 export and other music formats (M4A, AAC, …), install [ffmpeg](https://ffmpeg.org),
for example with `winget install ffmpeg`, then restart the game.

On an Intel Mac or Linux, run from source (below).

## Run from source

For developers, or on computers without a ready-made app. You only do steps 1–4 once.

1. **Install Miniforge** (a small Python distribution) from
   [github.com/conda-forge/miniforge](https://github.com/conda-forge/miniforge#install).
   Close and reopen your terminal afterwards.
2. **Get the code**: on this page click the green **Code** button → **Download ZIP** and unzip it,
   or use git:

   ```bash
   git clone https://github.com/Sanitysr163216/pixel-color-by-number.git
   ```

3. **Open a terminal in the project folder.** Type `cd ` (with a space), drag the unzipped folder
   into the terminal window and press Return. On Windows, use **Miniforge Prompt** from the Start menu
   as the terminal.
4. **Create the environment** (downloads about 1 GB, takes a few minutes):

   ```bash
   conda env create --file environment.yml
   ```

5. **Start the game**:

   ```bash
   conda activate color-number
   python main.py
   ```

Next time, only step 5 is needed. On macOS you can also double-click the
**Color Number.app** inside the project folder: it is a small launcher that starts `main.py` with the
`color-number` environment (keep it inside the project folder). After pulling new changes, run
`conda env update --file environment.yml`.

### Build the app yourself (macOS)

```bash
conda activate color-number
conda install -c conda-forge pyinstaller     # only needed once
packaging/build_macos.sh
```

The version number comes from `colornumber/__init__.py`. The app and a zip for GitHub Releases appear in `dist/`. The build uses PyInstaller and
does not include ffmpeg.

### Build the web version (phones)

The phone version lives in `web/` (HTML, CSS and JavaScript). `packaging/build_web.py` copies it to `site/` and
exports the built-in pictures, interface text and icons from the Python code, so both versions share them.
Photo conversion runs the unchanged `converter.py` in the browser with [Pyodide](https://pyodide.org).

```bash
python packaging/build_web.py
python -m http.server --directory site 8000      # then open http://localhost:8000
```

The [`web.yml`](.github/workflows/web.yml) workflow builds it and publishes it to GitHub Pages on every push to `main`.

### Build the Windows app

PyInstaller can only build a Windows app on Windows. The GitHub Actions workflow
[`windows.yml`](.github/workflows/windows.yml) does it automatically: it runs the tests, tries the game,
builds `Color-Number-<version>-Windows-x64.zip`, and adds it to the release when a `v…` tag is pushed.
You can also start it by hand under **Actions → Windows build → Run workflow**.

To build on your own Windows PC (in PowerShell, with Python 3.12):

```powershell
pip install -r packaging/requirements-windows.txt
packaging/build_windows.ps1
```

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
| Full screen | `Ctrl+Cmd+F` or `F11` (`F11` on Windows) |

On touch screens: one finger paints, two fingers zoom and pan.

## Where files are stored

- Saved pictures and settings: `~/Library/Application Support/colornumber/` (macOS),
  `%APPDATA%\colornumber\` (Windows)
- Exports: `Pictures/Color Number` in your home folder

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
    library.py           built-in pictures and categories
    library_more.py      more built-in pictures, drawn with simple shapes
    online.py            online art search (Art Institute of Chicago API)
    artworks.py          built-in art pack (works offline)
    render.py            draws progress as an image
    export.py            PNG / GIF / MP4 export
    audio.py             synthesized sound effects and music
    music.py             music library: featured tracks and imported music
    i18n.py              English and Chinese interface text
  assets/music/          featured music (OGG) and credits.json
  assets/artworks/       built-in artworks and credits.json
  ui/                    Kivy interface: screens, zoomable canvas, dialogs, sound, trackpad gestures
packaging/               build scripts: macOS and Windows apps (PyInstaller), web version
web/                     phone/web version (PWA): HTML, CSS, JavaScript
.github/workflows/       Windows test and build on GitHub Actions
preview.py               preview a photo conversion from the command line
tests/                   automated tests (run `pytest`); ui_smoke.py clicks through the real app
exercises/               Python exercises that go with the project (in Chinese)
```

Code comments are written in Chinese: the project started as a way to learn Python.

## Tests

```bash
pytest
```

## Built-in art credits

The built-in artworks in `colornumber/assets/artworks/` come from the open-access collections of
[The Metropolitan Museum of Art](https://www.metmuseum.org/hubs/open-access) (public domain, CC0) and the
[National Palace Museum, Taipei](https://digitalarchive.npm.gov.tw/opendata) (CC BY 4.0, credited in the
museum's required format). The game's copies are resized; some are cropped to remove the photographer's color
charts and blank album pages. `packaging/fetch_artworks.py` downloads and prepares them, and
`credits.json` holds the credits shown in the game.

| Artwork | Artist | Credit and license |
|---|---|---|
| [Under the Wave off Kanagawa](https://www.metmuseum.org/art/collection/search/45434) | Katsushika Hokusai, ca. 1830–32 | Under the Wave off Kanagawa (Kanagawa oki nami ura), also known as The Great Wave, from the series Thirty-six Views of Mount Fuji (Fugaku sanjūrokkei), Katsushika Hokusai, ca. 1830–32. The Metropolitan Museum of Art, H. O. Havemeyer Collection, Bequest of Mrs. H. O. Havemeyer, 1929. Public domain (CC0). |
| [Night-Shining White](https://www.metmuseum.org/art/collection/search/39901) | Han Gan, ca. 750 | Night-Shining White, Han Gan, ca. 750. The Metropolitan Museum of Art, Purchase, The Dillon Fund Gift, 1977. Public domain (CC0). |
| [Wang Xizhi watching geese](https://www.metmuseum.org/art/collection/search/40081) | Qian Xuan, ca. 1295 | Wang Xizhi watching geese, Qian Xuan, ca. 1295. The Metropolitan Museum of Art, Ex coll.: C. C. Wang Family, Gift of The Dillon Fund, 1973. Public domain (CC0). |
| [Finches and bamboo](https://www.metmuseum.org/art/collection/search/39936) | Emperor Huizong, early 12th century | Finches and bamboo, Emperor Huizong, early 12th century. The Metropolitan Museum of Art, John M. Crawford Jr. Collection, Purchase, Douglas Dillon Gift, 1981. Public domain (CC0). |
| [Viewing plum blossoms by moonlight](https://www.metmuseum.org/art/collection/search/44638) | Ma Yuan, early 13th century | Viewing plum blossoms by moonlight, Ma Yuan, early 13th century. The Metropolitan Museum of Art, Gift of John M. Crawford Jr., in honor of Alfreda Murck, 1986. Public domain (CC0). |
| [Orchids](https://www.metmuseum.org/art/collection/search/40133) | Ma Lin, second quarter of the 13th century | Orchids, Ma Lin, second quarter of the 13th century. The Metropolitan Museum of Art, Ex coll.: C. C. Wang Family, Gift of The Dillon Fund, 1973. Public domain (CC0). |
| [Magpies and Hare](https://digitalarchive.npm.gov.tw/opendata/Pub/Detail/48?dep=P&mode=full) | Cui Bo, 1061 | 宋崔白雙喜圖 軸。國立故宮博物院，台北，CC BY 4.0 @ www.npm.gov.tw |
| [Peonies, from Immortal Blossoms in an Everlasting Spring](https://digitalarchive.npm.gov.tw/opendata/Pub/Detail/4954?dep=P&mode=full) | Giuseppe Castiglione (Lang Shining), Qing dynasty | 清郎世寧畫仙萼長春 冊 牡丹。國立故宮博物院，台北，CC BY 4.0 @ www.npm.gov.tw |
| [Poppies and Irises, from Immortal Blossoms in an Everlasting Spring](https://digitalarchive.npm.gov.tw/opendata/Pub/Detail/4958?dep=P&mode=full) | Giuseppe Castiglione (Lang Shining), Qing dynasty | 清郎世寧畫仙萼長春 冊 虞美人蝴蝶花。國立故宮博物院，台北，CC BY 4.0 @ www.npm.gov.tw |
| [Assembled Auspiciousness](https://digitalarchive.npm.gov.tw/opendata/Pub/Detail/3581?dep=P&mode=full) | Giuseppe Castiglione (Lang Shining), 1723 | 清郎世寧聚瑞圖 軸。國立故宮博物院，台北，CC BY 4.0 @ www.npm.gov.tw |
| [Picture for the New Year](https://digitalarchive.npm.gov.tw/opendata/Pub/Detail/1227?dep=P&mode=full) | Zhao Chang, Song dynasty | 宋趙昌歲朝圖 軸。國立故宮博物院，台北，CC BY 4.0 @ www.npm.gov.tw |
| [Palace Concert](https://digitalarchive.npm.gov.tw/opendata/Pub/Detail/5?dep=P&mode=full) | Anonymous (Tang dynasty), Tang dynasty | 唐人宮樂圖 軸。國立故宮博物院，台北，CC BY 4.0 @ www.npm.gov.tw |
| [Children at Play in an Autumn Garden](https://digitalarchive.npm.gov.tw/opendata/Pub/Detail/34?dep=P&mode=full) | Su Hanchen, Song dynasty | 宋蘇漢臣秋庭戲嬰圖 軸。國立故宮博物院，台北，CC BY 4.0 @ www.npm.gov.tw |
| [Travelers Among Mountains and Streams](https://digitalarchive.npm.gov.tw/opendata/Pub/Detail/1195?dep=P&mode=full) | Fan Kuan, Song dynasty | 宋范寬谿山行旅圖 軸。國立故宮博物院，台北，CC BY 4.0 @ www.npm.gov.tw |
| [Early Spring](https://digitalarchive.npm.gov.tw/opendata/Pub/Detail/47?dep=P&mode=full) | Guo Xi, 1072 | 宋郭熙早春圖 軸。國立故宮博物院，台北，CC BY 4.0 @ www.npm.gov.tw |
| [Xuezhualu, from Ten Fine Hounds](https://digitalarchive.npm.gov.tw/opendata/Pub/Detail/13636?dep=P&mode=full) | Giuseppe Castiglione (Lang Shining), Qing dynasty | 清郎世寧畫十駿犬雪爪盧 軸。國立故宮博物院，台北，CC BY 4.0 @ www.npm.gov.tw |
| [Wheat Field with Cypresses](https://www.metmuseum.org/art/collection/search/436535) | Vincent van Gogh, 1889 | Wheat Field with Cypresses, Vincent van Gogh, 1889. The Metropolitan Museum of Art, Purchase, The Annenberg Foundation Gift, 1993. Public domain (CC0). |
| [Sunflowers](https://www.metmuseum.org/art/collection/search/436524) | Vincent van Gogh, 1887 | Sunflowers, Vincent van Gogh, 1887. The Metropolitan Museum of Art, Rogers Fund, 1949. Public domain (CC0). |
| [Irises](https://www.metmuseum.org/art/collection/search/436528) | Vincent van Gogh, 1890 | Irises, Vincent van Gogh, 1890. The Metropolitan Museum of Art, Gift of Adele R. Levy, 1958. Public domain (CC0). |
| [Self-Portrait with a Straw Hat](https://www.metmuseum.org/art/collection/search/436532) | Vincent van Gogh, 1887 | Self-Portrait with a Straw Hat (obverse: The Potato Peeler), Vincent van Gogh, 1887. The Metropolitan Museum of Art, Bequest of Miss Adelaide Milton de Groot (1876-1967), 1967. Public domain (CC0). |
| [Oleanders](https://www.metmuseum.org/art/collection/search/436530) | Vincent van Gogh, 1888 | Oleanders, Vincent van Gogh, 1888. The Metropolitan Museum of Art, Gift of Mr. and Mrs. John L. Loeb, 1962. Public domain (CC0). |
| [Cypresses](https://www.metmuseum.org/art/collection/search/437980) | Vincent van Gogh, 1889 | Cypresses, Vincent van Gogh, 1889. The Metropolitan Museum of Art, Rogers Fund, 1949. Public domain (CC0). |
| [Young Woman with a Water Pitcher](https://www.metmuseum.org/art/collection/search/437881) | Johannes Vermeer, ca. 1662 | Young Woman with a Water Pitcher, Johannes Vermeer, ca. 1662. The Metropolitan Museum of Art, Marquand Collection, Gift of Henry G. Marquand, 1889. Public domain (CC0). |
| [The Harvesters](https://www.metmuseum.org/art/collection/search/435809) | Pieter Bruegel the Elder, 1565 | The Harvesters, Pieter Bruegel the Elder, 1565. The Metropolitan Museum of Art, Rogers Fund, 1919. Public domain (CC0). |
| [The Dance Class](https://www.metmuseum.org/art/collection/search/438817) | Edgar Degas, 1874 | The Dance Class, Edgar Degas, 1874. The Metropolitan Museum of Art, Bequest of Mrs. Harry Payne Bingham, 1986. Public domain (CC0). |
| [Mäda Primavesi](https://www.metmuseum.org/art/collection/search/436819) | Gustav Klimt, 1912–13 | Mäda Primavesi (1903–2000), Gustav Klimt, 1912–13. The Metropolitan Museum of Art, Gift of André and Clara Mertens, in memory of her mother, Jenny Pulitzer Steiner, 1964. Public domain (CC0). |
| [The Repast of the Lion](https://www.metmuseum.org/art/collection/search/438822) | Henri Rousseau (le Douanier), ca. 1907 | The Repast of the Lion, Henri Rousseau (le Douanier), ca. 1907. The Metropolitan Museum of Art, Bequest of Sam A. Lewisohn, 1951. Public domain (CC0). |

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
is CC0 (public domain); see the credits above. The built-in artworks in `colornumber/assets/artworks/` are CC0
(The Met) or CC BY 4.0 (National Palace Museum, Taipei); see the built-in art credits above.
