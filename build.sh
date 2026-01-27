#!/bin/bash

echo "🔨 Building Calling Agent with WhatsApp Feature..."

cd "/mnt/hgfs/Shared from ubuntu/calling agent/CallingAgent"

# Clean previous build
echo "🧹 Cleaning..."
rm -rf app/build/

# Build APK
echo "📦 Building APK..."
if [ -f "gradlew" ]; then
    ./gradlew assembleDebug
elif [ -f "gradlew.bat" ]; then
    # Windows
    ./gradlew.bat assembleDebug
else
    echo "❌ Gradle wrapper not found!"
    exit 1
fi

echo ""
echo "✅ BUILD COMPLETE!"
echo ""
echo "📱 APK Location:"
echo "   app/build/outputs/apk/debug/app-debug.apk"
echo ""
echo "📲 Install Command:"
echo "   adb install -r app/build/outputs/apk/debug/app-debug.apk"
