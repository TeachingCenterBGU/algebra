# Quarto/Pandoc Preview Kit (HE)

מטרה: תצוגת HTML מהירה ל-LaTeX בלי גישה לפרויקט המקורי.

## שימוש
1) שימו את קובץ ה-`.tex` בתוך `in/`.
2) Windows: הריצו `render.bat in\my.tex` (או לחיצה כפולה בלי פרמטר תשתמש בדוגמה).
   macOS/Linux: `bash render.sh in/my.tex`.
3) פתחו את `out/<שם>.html`.

אם יש Quarto מותקן — השימוש בפילטר `env-to-callout.lua` ייתן Callouts בסגנון האתר.
אם יש רק Pandoc — השימוש ב-`env-to-details.lua` ייתן בלוק מתקפל `<details>` דומה.
