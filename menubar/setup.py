from setuptools import setup

setup(
    app="bzzzt.py",
    options={
        "py2app": {
            "argv_emulation": True,
            "plist": {
                "LSUIElement": True
            },
            "packages": [
                "rumps",
                "requests"
            ]
        }
    },
    setup_requires=[
        "py2app"
    ]
)
