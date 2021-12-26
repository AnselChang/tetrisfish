echo Building to %1.zip

rem install requirements.txt, then come back.
cd ..
pip install pyinstaller==4.7
pip install zip-files
pip install gitchangelog
pip install pystache
pip install -r requirements.txt

cd bundle

pyinstaller -D tetrisfish.spec


rem Now do the changelog:
powershell git describe --abbrev=0 --tags $(git rev-list --tags --skip=1 --max-count=1) > last-tag.txt
set /p LASTTAG=<last-tag.txt

cd ..
rem incremental changelog
gitchangelog %LASTTAG%..HEAD > changelog.txt
rem full changelog
gitchangelog > bundle/dist/changelog.md

cd bundle
rem zip everything neatly.
zip-folder dist -f TetrisFish_%1_win -o TetrisFish_%1_win.zip

