// Принудительно светлая тема админки независимо от тёмного режима ОС/браузера.
// Jazzmin 3.x (Bootstrap 5.3) иначе подстраивается под системную тёмную тему.
(function () {
  function forceLight() {
    document.documentElement.setAttribute("data-bs-theme", "light");
    document.documentElement.style.colorScheme = "light";
  }
  forceLight();
  document.addEventListener("DOMContentLoaded", forceLight);
  window.addEventListener("load", forceLight);
})();
