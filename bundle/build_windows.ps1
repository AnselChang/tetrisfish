# run this as:
#./build_windows.ps1 20212912
$tagname= $args[0]
echo "Building to $tagname.zip"

# install requirements.txt, then come back.
cd ..
pip install -r requirements.txt
cd bundle
pip install -r build-requirements.txt

pyinstaller tetrisfish.spec

cd ..
# full changelog
gitchangelog > bundle/dist/changelog.md

cd bundle
# zip everything neatly.
zip-folder dist -f "TetrisFish_$($tagname)" -o "TetrisFish_$($tagname).zip"

