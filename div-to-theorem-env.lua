-- ממיר בלוקים מסוג ::: {.definition/.example/...} לסביבות LaTeX
-- חשוב: HTML צריך להישאר עם ה-DIV כדי ש-Quarto ייצר כותרות!
local targets = {
  "definition", "example", "exercise", "remark",
  "theorem", "lemma", "proposition", "corollary"
}

function Div(div)
  -- אם זה לא PDF - לא עושים כלום, מחזירים nil כדי להשאיר את ה-DIV כמו שהוא
  if not quarto.doc.isFormat("pdf") then
    return nil
  end

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