#!/bin/sh
mkdir -p dist/dmg
rm -r dist/dmg/*
cp -r dist/DiffCast.app dist/dmg
test -f dist/DiffCast.dmg && rm dist/DiffCast.dmg
create-dmg \
  --volname "DiffCast" \
  --volicon "diffcast/images/icon.icns" \
  --window-pos 200 120 \
  --window-size 800 400 \
  --icon-size 100 \
  --icon "DiffCast.app" 200 190 \
  --hide-extension "DiffCast.app" \
  --app-drop-link 600 185 \
  "dist/DiffCast.dmg" \
  "dist/dmg/"
