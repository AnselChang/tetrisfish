# run with bash build_mac_os.sh 20220418
echo Building to $1.zip

# install requirements.txt, then come back.
cd ..
pip install -r requirements.txt
cd bundle
pip install -r build-requirements.txt

pyinstaller tetrisfish_macos.spec

# paste entire changelog
cd ..
gitchangelog > bundle/dist/changelog.md

cd bundle
# zip everything neatly.
zip-folder dist -f TetrisFish_$1_mac -o TetrisFish_$1.zip

