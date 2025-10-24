-- מסיר כותרת מודגשת שמופיעה בתחילת סביבות כמו הגדרה/דוגמה וכו'
local target = pandoc.List{
  "definition","example","exercise","remark",
  "theorem","lemma","proposition","corollary"
}

local function has(cls) return target:find(cls) ~= nil end

local function strip_leading_title(inlines)
  -- אם הראשון Strong – להסיר אותו ואת הנקודה/רווח שאחריו (אם יש)
  if #inlines == 0 then return inlines end
  if inlines[1].t == "Strong" then
    table.remove(inlines,1)
    if #inlines > 0 and inlines[1].t == "Str" and (inlines[1].text == "." or inlines[1].text == "․") then
      table.remove(inlines,1)
    end
    if #inlines > 0 and inlines[1].t == "Space" then
      table.remove(inlines,1)
    end
  end
  return inlines
end

function Div(el)
  local cls = el.classes or {}
  for _,c in ipairs(cls) do
    if has(c) and #el.content > 0 and el.content[1].t == "Para" then
      el.content[1].content = strip_leading_title(el.content[1].content)
      break
    end
  end
  return el
end
