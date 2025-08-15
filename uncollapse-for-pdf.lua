-- Expand collapsed callouts when rendering to PDF
function Div(div)
  -- בדיקה תקינה לפורמט PDF (כולל writer LaTeX)
  if quarto.doc.isFormat("pdf") then
    if div.classes:includes("callout") then
      -- הסרי כל מאפיין שמפעיל קיפול
      if div.attributes["collapse"] ~= nil then
        div.attributes["collapse"] = nil
      end
      if div.attributes["collapsible"] ~= nil then
        div.attributes["collapsible"] = nil
      end
      return div
    end
  end
end
