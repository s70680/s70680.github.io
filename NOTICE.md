# Third-party notices

The same notices are shown in the app at https://s70680.github.io/sky/licenses.html

## Astronomy Engine
https://github.com/cosinekitty/astronomy

```
MIT License

Copyright (c) 2019-2023 Don Cross <cosinekitty@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## d3-celestial (star and constellation data)
https://github.com/ofrohn/d3-celestial

Embedded, converted from d3-celestial data files: star positions/magnitudes/colour indices (stars.6.json; XHIP, Anderson & Francis 2012, CDS/VizieR V/137D; Hipparcos © ESA), constellation lines, label positions and ranks (IAU data as modified by Olaf Frohn), and constellation boundaries (Davenhall & Leggett 1989, CDS/VizieR VI/49).

```
Copyright (c) 2015, Olaf Frohn
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```

## ESO "The Milky Way panorama" (Milky Way layer)
https://www.eso.org/public/images/eso0932a/

Credit: ESO/S. Brunier

Licence: Creative Commons Attribution 4.0 International (CC BY 4.0), https://creativecommons.org/licenses/by/4.0/ (ESO's terms: https://www.eso.org/public/copyright/).

The Milky Way layer (`MW_DATA` in `sky/index.html`) is derived from this image by `tools/milkyway/build_milkyway.py`: stars removed, sky background subtracted, smoothed, cut into five brightness levels and sampled at about 3,400 points; patches not connected to the Galactic plane (for example the Magellanic Clouds, M31, the Pleiades, the Orion Nebula and a planet that appears in the photograph) were removed. The image itself is not included in the app or in this repository. ESO and the photographer are not affiliated with this app and do not endorse it.

This layer replaces the Milky Way outlines from d3-celestial's mw.json (Jose R. Vieira, Milky Way Outline Catalog; no licence was stated by its author, see https://github.com/ofrohn/d3-celestial/issues/160), which the app embedded until 2026-10 and which are no longer included.

## Stellarium "Chinese" sky culture (traditional Chinese star names)
https://github.com/Stellarium/stellarium/tree/master/skycultures/chinese

The traditional Chinese star names shown in the app (e.g. 天狼, 參宿七, 河鼓二) come from the Stellarium "Chinese" sky culture, via d3-celestial's `starnames.cn.json`, converted to Traditional Chinese characters by this project. Authors: Karrie Berglund (Digitalis Education Solutions, Inc.); extended by Sun Shuwei based on Yi Shitong, *Chinese and Western Contrast Star Chart and Catalogue 1950.0*.
Licence: Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0), https://creativecommons.org/licenses/by-sa/4.0/
This project's adapted star-name table (extraction, conversion to Traditional characters, mapping to catalogue numbers) is likewise offered under CC BY-SA 4.0. The rest of the app (code and Chinese descriptions) is not covered by this licence.

## Fonts
Noto Serif TC (© Google LLC / Adobe) and IBM Plex Mono (© IBM Corp.), SIL Open Font License 1.1 (https://openfontlicense.org/). Loaded at run time from Google Fonts; not bundled in this repository.
