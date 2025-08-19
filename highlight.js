document.addEventListener("DOMContentLoaded", () => {
  // בדוק אם יש פרמטר חיפוש בכתובת (search-highlighter)
  const params = new URLSearchParams(window.location.search);
  const q = params.get("q");
  if (!q) return;

  // נבנה ביטוי רגולרי מחיפוש
  const regex = new RegExp(q, "gi");

  // נעבור על כל פסקאות ותיבות תוכן
  document.querySelectorAll("main p, main li").forEach(el => {
    el.innerHTML = el.innerHTML.replace(regex, match =>
      `<mark style="background-color: #fff3a0; padding:0 2px;">${match}</mark>`
    );
  });
});
