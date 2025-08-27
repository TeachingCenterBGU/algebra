@echo off
setlocal
set INFILE=%1
if "%INFILE%"=="" set INFILE=in\sample.tex
for %%F in ("%INFILE%") do set BASENAME=%%~nF
set OUTFILE=out\%BASENAME%.html

where quarto >nul 2>nul
if %ERRORLEVEL%==0 (
  echo Using Quarto...
  quarto render "%INFILE%" --to html --output "%OUTFILE%" --filters env-to-callout.lua --css preview.css --css rtl-baseline.css --css styles.css
  goto done
)

where pandoc >nul 2>nul
if %ERRORLEVEL%==0 (
  echo Using Pandoc...
  pandoc "%INFILE%" -o "%OUTFILE%" --standalone --mathjax --lua-filter=env-to-details.lua -M lang=he -M dir=rtl --css=preview.css --css=rtl-baseline.css --css=styles.css
  goto done
)

echo Install Quarto or Pandoc to preview.
exit /b 1

:done
echo Done -> %OUTFILE%
endlocal
