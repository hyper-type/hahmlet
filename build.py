from fontTools.designspaceLib import DesignSpaceDocument
from glyphsLib.cli import main
from fontTools.ttLib import TTFont, newTable
from pathlib import Path
import shutil, os
import ufo2ft
import ufoLib2
import statmake.classes
import statmake.lib
import subprocess
import fontmake.instantiator
import multiprocessing
import multiprocessing.pool

path = Path("sources")

def DSIG_modification(font:TTFont):
    font["DSIG"] = newTable("DSIG")     #need that stub dsig
    font["DSIG"].ulVersion = 1
    font["DSIG"].usFlag = 0
    font["DSIG"].usNumSigs = 0
    font["DSIG"].signatureRecords = []
    font["head"].flags |= 1 << 3        #sets flag to always round PPEM to integer

def autohint(file):
    print ("["+str(file).split("/")[2][:-4]+"] Autohinting")
    subprocess.check_call(
            [
                "ttfautohint",
                "--stem-width",
                "nsn",
                str(file),
                str(file)[:-4]+"-hinted.ttf",
            ]
        )
    shutil.move(str(file)[:-4]+"-hinted.ttf", str(file))


# Converting from Glyphs to UFO
print ("[Hahmlet] Converting to UFO")
main(("glyphs2ufo", "sources/hahmlet.glyphs", "--write-public-skip-export-glyphs", "--propagate-anchors"))

for ufo in path.glob("*.ufo"): # need to put this command in all the source UFOs to make sure it is implemented
    source = ufoLib2.Font.open(ufo)
    source.lib['com.github.googlei18n.ufo2ft.filters'] = [{
         "name": "flattenComponents",
         "pre": 1,
     }]
    ufoLib2.Font.save(source)

# Load designspace and prepare for ACTION
designspace = DesignSpaceDocument.fromfile("sources/hahmlet.designspace")
designspace.loadSourceFonts(ufoLib2.Font.open)

# Create variable font
print ("[Hahmlet Variable] Creating variable font")

varFont = ufo2ft.compileVariableTTF(designspace)

varFont["name"].setName("함렡", 1, 3, 1, 1042) # for whatever reason ufo2ft doesn't implement localized names, so we add them here
varFont["name"].setName("함렡", 4, 3, 1, 1042)
varFont["name"].setName("Hahmlet", 4, 3, 1, 1033)
varFont["name"].setName("Hahmlet-Roman", 6, 3, 1, 1033)
varFont["name"].setName("함민주(한글), 마크프롬베르크(라틴)", 9, 3, 1, 1042)
varFont["name"].setName("Roman", 17, 3, 1, 1042)
varFont["name"].setName("HahmletRoman", 25, 3, 1, 1042)

styleSpace = statmake.classes.Stylespace.from_file("sources/STAT.plist")
statmake.lib.apply_stylespace_to_variable_font(styleSpace, varFont, {})
DSIG_modification(varFont)
del varFont["MVAR"] # until the beautiful future when MVAR doesn't cause problems, it has been diabled. :(
varFont.save("fonts/variable/Hahmlet[wght].ttf")

autohint(Path("fonts/variable/Hahmlet[wght].ttf"))


# Create static instances
print ("[Hahmlet] Building Static Instances")

generator = fontmake.instantiator.Instantiator.from_designspace(designspace)

def make_static(instance_descriptor):
    instance = generator.generate_instance(instance_descriptor)

    instance.lib['com.github.googlei18n.ufo2ft.filters'] = [{ # extra safe :)
        "name": "flattenComponents",
        "pre": 1,
    }]

    # ufo2ft can't generate the panose values from the customParameters, so we have to insert it ourselves
    for param in instance_descriptor.lib["com.schriftgestaltung.customParameters"]:
        if param[0] == "panose":
            instance.info.openTypeOS2Panose = param[1]

    static_ttf = ufo2ft.compileTTF(
        instance, 
        removeOverlaps=True, 
        overlapsBackend="pathops", 
        useProductionNames=True,
    )

    style_name = instance.info.styleName
    family_name = instance.info.familyName

    if style_name is "Regular" or style_name is "Bold":
        static_ttf["name"].setName("함렡", 1, 3, 1, 1042)
    else:
        static_ttf["name"].setName("함렡 "+style_name, 1, 3, 1, 1042)
        static_ttf["name"].setName("함렡", 16, 3, 1, 1042)

    static_ttf["name"].setName("함렡 "+style_name, 4, 3, 1, 1042)
    static_ttf["name"].setName("함민주(한글), 마크프롬베르크(라틴)", 9, 3, 1, 1042)

    DSIG_modification(static_ttf)
    print ("[Hahmlet "+str(style_name).replace(" ","")+"] Saving")
    output = "fonts/ttf/"+family_name+"-"+str(style_name).replace(" ","")+".ttf"
    static_ttf.save(output)
    autohint(output)

pool = multiprocessing.pool.Pool(processes=multiprocessing.cpu_count())
processes = []

for instance_descriptor in designspace.instances: # GOTTA GO FAST
    processes.append(
        pool.apply_async(
            make_static,
            (
                instance_descriptor,
            ),
        )
    )

pool.close()
pool.join()
for process in processes:
    process.get()
del processes, pool

# Cleanup
for ufo in path.glob("*.ufo"):
    shutil.rmtree(ufo)
os.remove("sources/hahmlet.designspace")