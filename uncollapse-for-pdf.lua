-- uncollapse-for-pdf.lua

-- פונקציה זו תופעל על כל אלמנט מסוג Div במסמך
function Div(div)
  -- אנחנו מבצעים את השינוי רק כאשר הפורמט הוא PDF
  if quarto.FORMAT == "pdf" then
    -- בדוק אם ל-Div יש את הקלאס 'callout' ואת התכונה 'collapse'
    if div.classes:includes("callout") and div.attributes.collapse then
      -- אם כן, פשוט הסר את התכונה 'collapse'
      -- על ידי הגדרתה ל-nil (כלומר, לא קיימת)
      div.attributes.collapse = nil
      -- החזר את ה-Div המעודכן
      return div
    end
  end
end