#outputs incremental changelog to project root
# Now do the changelog:
pip install gitchangelog
pip install pystache
powershell git describe --abbrev=0 --tags $(git rev-list --tags --skip=1 --max-count=1) > last-tag.txt
$LastTag = (Get-Content last-tag.txt)

cd ..
# incremental changelog
gitchangelog "$LastTag..HEAD" > changelog.txt