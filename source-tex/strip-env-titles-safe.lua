
-- strip-env-titles-plus.lua
-- Robustly remove a leading label (e.g., "דוגמה 1.8." / "Example 2.4:") from the
-- first paragraph of theorem-like blocks, while preserving inline structure.

local ENV_CLASSES = {
  definition=true, example=true, exercise=true, remark=true,
  theorem=true, lemma=true, proposition=true, corollary=true, proof=true,
  note=true, property=true, observation=true
}

-- Include common alternative class names that sometimes appear after conversions
local ALT_CLASSES = {
  def=true, ex=true, exm=true, exmp=true, thm=true, lem=true, prop=true, cor=true, rm=true
}

-- Keywords that may start the label (Hebrew + English)
local KEYWORDS = {
  ["דוגמה"]=true, ["תרגיל"]=true, ["משפט"]=true, ["הגדרה"]=true, ["הערה"]=true,
  ["Example"]=true, ["Exercise"]=true, ["Theorem"]=true, ["Definition"]=true, ["Remark"]=true,
  ["Lemma"]=true, ["Proposition"]=true, ["Corollary"]=true, ["Proof"]=true, ["Note"]=true, ["Property"]=true, ["Observation"]=true
}

local function has_theorem_class(div)
  for cls, _ in pairs(ENV_CLASSES) do
    if div.classes:includes(cls) then return true end
  end
  for cls, _ in pairs(ALT_CLASSES) do
    if div.classes:includes(cls) then return true end
  end
  return false
end

-- Does inline represent a (non-breaking) space of any kind?
local function isSpaceLike(el)
  return (el and (el.t == "Space" or el.t == "SoftBreak" or (el.t == "Str" and el.text:match("^[%s\194\160]+$"))))
end

-- Is a Str element consisting only of digits/dots/colons/underscores/hyphens
local function isDigitsToken(el)
  return (el and el.t == "Str" and el.text:match("^[%d%._:%-]+$") ~= nil)
end

-- Unwrap containers like Strong/Emph/Span at the *beginning* so we can see raw tokens
local WRAPS = { Strong=true, Emph=true, SmallCaps=true, Superscript=true, Subscript=true, Span=true, Strikeout=true }
local function unwrap_prefix(inlines, i)
  local el = inlines[i]
  if not el then return {inlines[i]}, i end
  if WRAPS[el.t] then
    if el.content and #el.content > 0 then
      return el.content, i
    end
  end
  return {el}, i
end

-- Consume leading label: KEYWORD [space] [digits tokens]+ [optional "." or ":"] [optional space]
local function consume_label(inlines)
  local i = 1
  local prefix, at = unwrap_prefix(inlines, i)
  local first = prefix[1]
  if not (first and first.t == "Str" and KEYWORDS[first.text]) then
    return 0
  end

  i = at + 1

  if isSpaceLike(inlines[i]) then i = i + 1 end

  local anyDigits = false
  while isDigitsToken(inlines[i]) do
    anyDigits = true
    i = i + 1
  end

  if inlines[i] and inlines[i].t == "Str" and (inlines[i].text == "." or inlines[i].text == ":") then
    i = i + 1
  end

  if isSpaceLike(inlines[i]) then i = i + 1 end

  if anyDigits then
    return i - 1
  end

  if inlines[i-1] and inlines[i-1].t == "Str" and (inlines[i-1].text == "." or inlines[i-1].text == ":") then
    return i - 1
  end

  return 0
end

local function strip_first_paragraph_label(div)
  if #div.content == 0 then return div end
  local first = div.content[1]
  if first.t ~= "Para" and first.t ~= "Plain" then return div end

  local inl = first.content
  local consumed = consume_label(inl)

  if consumed > 0 then
    local kept = {}
    for j = consumed + 1, #inl do
      kept[#kept+1] = inl[j]
    end
    div.content[1] = (first.t == "Para") and pandoc.Para(kept) or pandoc.Plain(kept)
  end
  return div
end

function Div(div)
  if has_theorem_class(div) then
    return strip_first_paragraph_label(div)
  end
  return nil
end
