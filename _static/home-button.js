// Adds a house icon after the search bar that returns to neurodesk.org, like the Jupyter Book 1
// icon link, and points the bold "Neurodesk" project title at the top of the sidebar there too
// (the header logo already links to the NeurodeskEDU homepage). The page is rendered by React,
// so both are re-applied if a re-render drops them.
(() => {
  const house = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" '
    + 'aria-hidden="true" class="h-full w-full p-[18%]"><path d="M11.47 3.841a.75.75 0 0 1 1.06 0l8.69 8.69a.75.75 '
    + '0 1 0 1.06-1.061l-8.689-8.69a2.25 2.25 0 0 0-3.182 0l-8.69 8.69a.75.75 0 1 0 1.061 1.06l8.69-8.689Z"/>'
    + '<path d="m12 5.432 8.159 8.159c.03.03.06.058.091.086v6.198c0 1.035-.84 1.875-1.875 1.875H15a.75.75 0 0 '
    + '1-.75-.75v-4.5a.75.75 0 0 0-.75-.75h-3a.75.75 0 0 0-.75.75V21a.75.75 0 0 1-.75.75H5.625a1.875 1.875 0 0 '
    + '1-1.875-1.875v-6.198a2.29 2.29 0 0 0 .091-.086L12 5.432Z"/></svg>';

  const home = "https://neurodesk.org";
  const projectTitle = ".myst-toc > a.myst-toc-item:first-child";

  function sync() {
    for (const link of document.querySelectorAll(projectTitle)) {
      if (link.href !== home + "/") link.href = home;
    }

    const search = document.querySelector(".myst-search-bar");
    // Adding nodes before React hydrates the header would make hydration fail.
    if (!search || !Object.keys(search).some((key) => key.startsWith("__reactFiber"))) return;
    if (search.parentElement.querySelector(".nd-home-button")) return;
    // Reuse the theme toggle's own utility classes: they live in the theme's versioned stylesheet,
    // so the button matches the toggle exactly and can't be broken by a stale cached myst-theme.css.
    // Hidden on phones, where the header has no room for it; the sidebar title covers that case.
    const link = Object.assign(document.createElement("a"), {
      href: home, title: "Return to neurodesk.org",
      className: "nd-home-button hidden md:block shrink-0 rounded-full border border-myst-border-strong "
        + "hover:bg-myst-surface border-solid overflow-hidden text-myst-text-secondary w-8 h-8 ml-3",
    });
    link.setAttribute("aria-label", "Return to neurodesk.org");
    link.innerHTML = house;
    search.after(link);
  }

  setInterval(sync, 250);
  // The theme's router handles clicks on its own links and ignores the changed href, so catch the
  // project title click first and leave the site.
  document.addEventListener("click", (event) => {
    if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    if (!event.target.closest(projectTitle)) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    location.href = home;
  }, true);
})();
