/* Click-to-load Google Maps and YouTube: a button in .ali-map puts the iframe in. */
document.addEventListener("click", function (e) {
  var btn = e.target.closest && e.target.closest(".ali-map__btn");
  if (!btn) return;
  var box = btn.closest(".ali-map");
  var frame = document.createElement("iframe");
  frame.src = box.getAttribute("data-src");
  frame.title = box.getAttribute("data-title") || "";
  if (box.getAttribute("data-allow")) frame.setAttribute("allow", box.getAttribute("data-allow"));
  frame.setAttribute("allowfullscreen", "");
  box.classList.add("ali-map--loaded");
  box.textContent = "";
  box.appendChild(frame);
});
