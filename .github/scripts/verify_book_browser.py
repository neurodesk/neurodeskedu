#!/usr/bin/env python3
"""Verify section lists, menus, downloads, redirects, and optional saved widgets."""

import argparse
from pathlib import PurePosixPath
import re
from urllib.parse import urlsplit
from playwright.sync_api import expect, sync_playwright


def verify_section_navigation(page, url: str, routes: dict[str, str]) -> None:
    """Section landing pages must list their own pages, not the whole project."""
    sections = [source for source in routes if source.endswith("/intro.md")
                and source not in {"examples/intro.md", "tutorials/intro.md"}]
    for source in sections:
        folder = PurePosixPath(source).parent
        expected = {urlsplit(url + "/" + route).path.rstrip("/")
                    for child, route in routes.items()
                    if child != source and PurePosixPath(child).parent == folder}
        page.goto(url + "/" + routes[source], wait_until="domcontentloaded")
        links = page.locator("article ul a")
        expect(links, f"{source} must list only its own pages").to_have_count(len(expected))
        actual = {urlsplit(href).path.rstrip("/")
                  for href in links.evaluate_all("els => els.map(el => el.href)")}
        assert actual == expected, f"{source} lists pages outside its section: {actual ^ expected}"

    # Exercise actual sidebar links and disclosure buttons at desktop and phone sizes.
    functional_source = "tutorials/functional_imaging/intro.md"
    functional_count = sum(child != functional_source
                           and PurePosixPath(child).parent == PurePosixPath(functional_source).parent
                           for child in routes)
    for width in (1440, 390):
        page.set_viewport_size({"width": width, "height": 1000})
        page.goto(url + "/" + routes["tutorials/intro.md"], wait_until="domcontentloaded")
        menu = page.get_by_role("button", name="Open Menu", exact=True)
        if menu.is_visible():
            menu.click()
        toc = page.locator(".myst-toc:visible")
        section = toc.get_by_role("link", name="Functional Imaging", exact=True)
        row = section.locator("..")
        toggle = row.get_by_role("button", name="Open Folder", exact=True)
        expect(toggle).to_have_attribute("aria-expanded", "false")
        before = page.url
        toggle.click()
        expect(toggle).to_have_attribute("aria-expanded", "true")
        assert page.url == before, "Opening a folder navigated away"
        toggle.click()
        expect(toggle).to_have_attribute("aria-expanded", "false")
        expect(toc.get_by_role("link", name="Examples", exact=True).locator("..")
               .get_by_role("button")).to_have_attribute("aria-expanded", "false")
        section.click()
        expect(page).to_have_url(url + "/" + routes[functional_source])
        expect(page.locator("article ul a")).to_have_count(functional_count)
        if menu.is_visible():
            menu.click()
        toc.get_by_role("link", name="PhysIO", exact=True).click()
        expect(page).to_have_url(url + "/" + routes["tutorials/functional_imaging/physio.md"])
        expect(page.get_by_role("heading", name="PhysIO", exact=True)).to_be_visible()
        page.go_back(wait_until="domcontentloaded")
        expect(page.locator("article ul a")).to_have_count(functional_count)
    page.set_viewport_size({"width": 1440, "height": 1000})
    print(f"Verified {len(sections)} section lists and desktop/mobile sidebar navigation")


def verify(url: str, executable: str | None, widgets: bool, screenshot: str | None) -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=executable, args=["--enable-unsafe-swiftshader"])
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        response = page.request.get(url + "/neurodesk-pages.json")
        assert response.ok, "Missing page inventory"
        routes = response.json()
        verify_section_navigation(page, url, routes)
        # Exercise a page with lossless PNGs and SVG screenshot guides. Its server
        # markup must hydrate with the same image structure as client navigation.
        for source, count in [("tutorials/spectroscopy/fsl-mrs.md", 8),
                              ("tutorials/electrophysiology/EEG_mne-python.md", 9)]:
            page.goto(url + "/" + routes[source], wait_until="domcontentloaded")
            expect(page.locator("article img")).to_have_count(count)
            for image in page.locator("article img").all():
                expect(image).to_have_js_property("naturalWidth", 1280)
        source = "examples/structural_imaging/brain_extraction_different_tools.ipynb"
        notebook_url = url + "/" + routes[source]
        page.goto(notebook_url, wait_until="domcontentloaded")
        expect(page.locator(".nd-launch")).to_have_count(1)
        page.locator(".myst-fm-block-header .nd-launch-menu summary").click()
        launches = page.locator('.nd-launch-menu a[href*="/hub/user-redirect/git-pull?"]')
        expect(launches).to_have_count(5)
        expect(page.locator(".nd-launch")).to_be_hidden()
        for launch in launches.all():
            expect(launch).to_be_visible()

        page.get_by_role("button", name="Downloads").click()
        download = page.get_by_role("link", name="Download Download source notebook")
        expect(download).to_be_visible()
        raw_url = url + "/_sources/" + source
        assert download.evaluate("el => el.href") == raw_url, "Download menu points to the wrong source"
        fetched = page.request.get(raw_url)
        assert fetched.ok, "Raw download failed"
        raw = fetched.json()
        assert "nd-launch" not in str(raw), "Download includes generated controls"
        page.keyboard.press("Escape")

        toc = page.locator(".myst-toc:visible")
        toc.get_by_role("link", name=re.compile("^Structural imaging$", re.IGNORECASE)).click()
        expect(page.locator(".nd-launch")).to_have_count(0)
        expect(page.locator(".nd-launch-menu")).to_have_count(0)
        expect(page.locator(".nd-review-badge")).to_have_count(0)
        page.go_back(wait_until="domcontentloaded")
        expect(page.locator(".nd-launch")).to_have_count(1)
        expect(page.locator(".nd-launch-menu")).to_have_count(1)

        if widgets:
            frames = page.locator('iframe[title="Interactive notebook output"]')
            expect(frames).to_have_count(5)
            for frame in frames.all():
                frame.scroll_into_view_if_needed()
                expect(frame.content_frame.locator("canvas")).to_be_visible(timeout=60000)
            frames.first.scroll_into_view_if_needed()
        if screenshot:
            page.screenshot(path=screenshot)
        assert not errors, errors

        if "tutorials/about_neurodesk/RISE_slideshow.ipynb" in routes:
            target = routes["tutorials/about_neurodesk/RISE_slideshow.ipynb"]
            page.goto(url + "/examples/workflows/RISE_slideshow.html?check=1#test", wait_until="domcontentloaded")
            page.wait_for_url(url + "/" + target + "?check=1#test")
            print("Verified the legacy RISE redirect with its query and fragment")
        browser.close()
        print("Verified launch menu, raw download, page navigation, and Back")
        if widgets:
            print("Verified all five saved NiiVue canvases")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    parser.add_argument("--browser-executable")
    parser.add_argument("--widgets", action="store_true")
    parser.add_argument("--screenshot")
    args = parser.parse_args()
    verify(args.url.rstrip("/"), args.browser_executable, args.widgets, args.screenshot)
