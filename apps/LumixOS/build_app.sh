#!/bin/zsh
# build_app.sh: build LumixOS.app (release) next to this script. Needs the repo .venv (camera service) to run.
set -e
cd ${0:a:h}
swift build -c release
APP=LumixOS.app
rm -rf $APP && mkdir -p $APP/Contents/MacOS
cp .build/release/LumixOS $APP/Contents/MacOS/LumixOS
cat > $APP/Contents/Info.plist <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleName</key><string>LumixOS</string>
<key>CFBundleIdentifier</key><string>local.lumixos.app</string>
<key>CFBundleExecutable</key><string>LumixOS</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>CFBundleShortVersionString</key><string>0.1</string>
<key>LSMinimumSystemVersion</key><string>14.0</string>
<key>NSHighResolutionCapable</key><true/>
</dict></plist>
PLIST
codesign --force -s - $APP
echo "built $PWD/$APP"
