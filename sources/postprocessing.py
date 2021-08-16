#!/usr/bin/env python3
"""Fix the font names for the variable fonts"""
# TODO (M Foley) this shouldn't be required. Send fix to fontmake
from fontTools.ttLib import TTFont
from glob import glob
import os, shutil

font_paths = glob("fonts/**/*")

for path in font_paths:
	font = TTFont(path)

	font["name"].setName("함렡", 1, 3, 1, 1042)
	font["name"].setName("함렡", 4, 3, 1, 1042)
	font["name"].setName("함민주(한글), 마크프롬베르크(라틴)", 9, 3, 1, 1042)

	font.save(path + ".fix")

	shutil.move(path + ".fix", path)