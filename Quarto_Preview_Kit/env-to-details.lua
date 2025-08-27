-- env-to-details.lua
function Div(div)
  local is_solution = div.classes:includes("solution")
  local is_hint = div.classes:includes("hint")
  if is_solution or is_hint then
    local title = is_solution and "הצג פתרון" or "רמז"
    local inner = pandoc.Blocks(div.content)
    local open = pandoc.RawBlock("html", '<details class="' .. (is_solution and "solution" or "hint") .. '">')
    local summary = pandoc.RawBlock("html", "<summary>" .. title .. "</summary>")
    local close = pandoc.RawBlock("html", "</details>")
    local blocks = pandoc.List{ open, summary }
    for i = 1, #inner do blocks:insert(inner[i]) end
    blocks:insert(close)
    return blocks
  end
end
