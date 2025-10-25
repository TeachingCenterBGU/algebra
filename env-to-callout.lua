-- Map LaTeX environments \begin{solution}...\end{solution} and \begin{hint}...\end{hint}
-- to Quarto callouts when rendering HTML. No effect in PDF.
function Div(div)
  if not quarto.doc.isFormat("pdf") then
    if div.classes:includes("solution") then
      -- קובעים מחלקות נקיות: בלי proof
      div.classes = pandoc.List({ "callout", "callout-note", "solution" })
      div.attributes["collapse"] = "true"
      div.attributes["title"] = "הצג פתרון"
      return div
    elseif div.classes:includes("hint") then
      div.classes = pandoc.List({ "callout", "callout-tip", "hint" })
      div.attributes["collapse"] = "true"
      div.attributes["title"] = "רמז"
      return div
    end
  end
end