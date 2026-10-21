// Shows the page's "Run this notebook" links as a rocket menu in the page header, like the
// Jupyter Book 1 launch button. The links come from the .nd-launch dropdown that the build adds to
// notebook pages, so the menu follows client-side navigation between pages.
(() => {
  const rocket = '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" '
    + 'stroke="currentColor" width="1.25rem" height="1.25rem" aria-hidden="true"><path stroke-linecap="round" '
    + 'stroke-linejoin="round" d="M15.59 14.37a6 6 0 0 1-5.84 7.38v-4.8m5.84-2.58a14.98 14.98 0 0 0 '
    + '6.16-12.12A14.98 14.98 0 0 0 9.631 8.41m5.96 5.96a14.926 14.926 0 0 1-5.841 2.58m-.119-8.54a6 6 0 0 '
    + '0-7.381 5.84h4.8m2.581-5.84a14.927 14.927 0 0 0-2.58 5.84m2.699 2.7c-.103.021-.207.041-.311.06a15.09 '
    + '15.09 0 0 1-2.448-2.448 14.9 14.9 0 0 1 .06-.312m-2.24 2.39a4.493 4.493 0 0 0-1.757 4.306 4.493 4.493 '
    + '0 0 0 4.306-1.758M16.5 9a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0Z"/></svg>';

  function sync() {
    const header = document.querySelector(".myst-fm-block-header");
    // Adding nodes before React hydrates the header would make hydration fail.
    if (!header || !Object.keys(header).some((key) => key.startsWith("__reactFiber"))) return;
    const links = [...document.querySelectorAll(".nd-launch a[href]")];
    const key = links.map((link) => link.href).join(" ");
    let menu = header.querySelector(".nd-launch-menu");
    if (menu && menu.dataset.links === key) return;
    menu?.remove();
    if (!links.length) return;
    menu = document.createElement("details");
    menu.className = "nd-launch-menu";
    menu.dataset.links = key;
    menu.innerHTML = `<summary title="Run this notebook on a Neurodesk Play server">${rocket}<span>Launch</span>`
      + '</summary><ul aria-label="Run this notebook"></ul>';
    for (const link of links) {
      const item = document.createElement("li");
      item.append(Object.assign(document.createElement("a"), {
        href: link.href, textContent: link.textContent, target: "_blank", rel: "noopener noreferrer",
      }));
      menu.lastChild.append(item);
    }
    header.append(menu);
  }

  setInterval(sync, 250);
  document.addEventListener("click", (event) => {
    for (const menu of document.querySelectorAll(".nd-launch-menu[open]")) {
      if (!menu.contains(event.target)) menu.open = false;
    }
  });
})();
