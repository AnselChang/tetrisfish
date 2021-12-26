Please read the instructions carefully before starting!

Running/Development
===
You can choose to create a virtualenv (recommended) or do it in your raw Python installation.

Running with virtualenv:
===

1) Install virtual environment and requirements. First, we create a virtual environment
```
python -m venv venv
cd venv/scripts
activate
cd ../..
pip install -r requirements.txt
```

2) After this is done (once only), you can run the app.
Activate the virtual environment if you aren't in it, then use

`python main.py`

Running without virtualenv:
===

1) Install requirements. `pip install -r requirements.txt`
2) `python main.py`



Building
===
Building is via pyinstaller

0) If using a virtual env, activate it.

1) Install pyinstaller:  `pip install pyinstaller`

2) `cd bundle` then build.

3) `pyinstaller <whatever>.spec`


Auto-Building
===
Simply tag a commit in the format YYYYMMDD, and push this tag to github.
A draft release will show up in the draft page.

Anything that matches `^202.*$`, so you can use YYYYMMDD_v2 for multiple on same day.