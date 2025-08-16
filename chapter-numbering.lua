-- chapter-numbering.lua
-- שני הפרקים הראשונים במספור רומאי; מהשלישי מספור רגיל שמתחיל מ-1 (PDF בלבד)
local chap = 0

function Header(el)
  if not quarto.doc.isFormat("pdf") then return nil end
  if el.level ~= 1 then return nil end  -- תופס רק כותרות פרק (H1)
  chap = chap + 1

  if chap == 1 then
    -- לפני הפרק הראשון: העבר למספור רומאי
    return { pandoc.RawBlock('latex', '\\renewcommand{\\thechapter}{\\Roman{chapter}}'), el }
  elseif chap == 3 then
    -- לפני הפרק השלישי: חזרה לארבי והתחלה מ-1
    return { pandoc.RawBlock('latex', '\\renewcommand{\\thechapter}{\\arabic{chapter}}\\setcounter{chapter}{0}'), el }
  else
    return nil
  end
end
