# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Xiangyu Lyu and the Jiuye Yingzao contributors
"""Build jiuye_yingzao.zip (installable add-on / extension) at the repository root. Run: py -3.12 tools/package.py"""
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]; SRC = ROOT / 'jiuye_yingzao'
EXTRA = ['LICENSE', 'LICENSING.md']                    # shipped inside the add-on folder of the zip


def main():
    out = ROOT / 'jiuye_yingzao.zip'; n = 0
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for f in sorted(SRC.rglob('*')):
            if f.is_file() and '__pycache__' not in f.parts:
                z.write(f, f.relative_to(ROOT).as_posix()); n += 1
        for name in EXTRA:
            z.write(ROOT / name, f'jiuye_yingzao/{name}'); n += 1
    print(out, n, 'files', round(out.stat().st_size / 2 ** 20, 1), 'MB')


if __name__ == '__main__':
    main()
