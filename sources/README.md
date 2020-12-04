Instructions:

For OTF and TTF we provide different sets of instances, because of the empty Hangeul glyphs in the OTFs.

For OTF:
- Activate the OTF instances and deactivate the TTF instances.
- Then generate from FontMake:
`fontmake -g Hahmlet.glyphs -i -o otf`

For TTF:
- Activate the TTF instances and deactivate the OTF instances.
- Then generate from FontMake.
`fontmake -g Hahmlet.glyphs -i -o ttf`
