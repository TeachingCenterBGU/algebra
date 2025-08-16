-- div-to-theorem-env.lua
-- ממיר בלוקים מסוג ::: {.definition/.example/...} לסביבות LaTeX
local targets = {
  "definition", "example", "exercise",
  "theorem", "lemma", "proposition", "corollary"
}

local function includes(tbl, val)
  for _, v in ipairs(tbl) do if v == val then return true end end
  return false
end

function Div(div)
  for _, cls in ipairs(targets) do
    if div.classes:includes(cls) then
      local out = pandoc.List()
      out:insert(pandoc.RawBlock('latex', '\\begin{' .. cls .. '}'))
      if div.identifier and div.identifier ~= '' then
        out:insert(pandoc.RawBlock('latex', '\\label{' .. div.identifier .. '}'))
      end
      for _, b in ipairs(div.content) do out:insert(b) end
      out:insert(pandoc.RawBlock('latex', '\\end{' .. cls .. '}'))
      return out
    end
  end
  return nil
end
