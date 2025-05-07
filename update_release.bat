@echo off
:: Cross-platform build and publish script for Windows CMD

:: Clean old build artifacts
echo Cleaning up old build files...
rmdir /s /q dist 2>nul
rmdir /s /q build 2>nul
rmdir /s /q *.egg-info 2>nul

:: Rebuild the package
echo Building the package...
python -m build
if %errorlevel% neq 0 (
    echo Build failed. Exiting...
    exit /b %errorlevel%
)

:: Upload to PyPI
echo Uploading the package to PyPI...
twine upload dist/*
if %errorlevel% neq 0 (
    echo Upload failed. Exiting...
    exit /b %errorlevel%
)

echo Package successfully uploaded.
exit /b 0