import asyncio
import random
from enum import Enum, auto
from playwright.async_api import Page


class Section(Enum):
    HOME = auto()
    SEARCH = auto()
    EXPLORE = auto()
    REELS = auto()
    MESSAGES = auto()
    NOTIFICATIONS = auto()
    CREATE = auto()
    PROFILE = auto()


_SIDEBAR_SVG = {
    Section.HOME:          "svg[aria-label='Home']",
    Section.SEARCH:        "svg[aria-label='Search']",
    Section.EXPLORE:       "svg[aria-label='Explore']",
    Section.REELS:         "svg[aria-label='Reels']",
    Section.MESSAGES:      "svg[aria-label='Messages']",
    Section.NOTIFICATIONS: "svg[aria-label='Notifications']",
    Section.CREATE:        "svg[aria-label='New post']",
}

_WAIT_AFTER = {
    Section.HOME:          "article, div[role='button'][aria-label*='Story by']",
    Section.SEARCH:        "input[aria-label='Search input']",
    Section.EXPLORE:       "a[href*='/p/'], a[href*='/reel/']",
    Section.REELS:         "video",
    Section.MESSAGES:      "input[name='searchInput'], div[aria-label='Thread list']",
    Section.NOTIFICATIONS: "div[role='button'][aria-label='Close']",
    Section.CREATE:        "div[role='dialog'], input[type='file']",
    Section.PROFILE:       "header section",
}


class Navigator:

    def __init__(self, page: Page, username: str = ""):
        self._page = page
        self._username = username
        self._current: Section | None = None

    @property
    def current_section(self) -> Section | None:
        return self._current


    @staticmethod
    async def _short():
        await asyncio.sleep(random.uniform(0.3, 0.8))

    @staticmethod
    async def _medium():
        await asyncio.sleep(random.uniform(0.8, 2.0))


    async def go_home(self):
        await self._sidebar_click(Section.HOME)
        await self._wait_after(Section.HOME)
        await self._medium()
        self._current = Section.HOME

    async def go_reels(self):
        await self._sidebar_click(Section.REELS)
        await self._wait_after(Section.REELS)
        await self._medium()
        self._current = Section.REELS

    async def go_explore(self):
        await self._sidebar_click(Section.EXPLORE)
        await self._wait_after(Section.EXPLORE)
        await self._medium()
        self._current = Section.EXPLORE

    async def go_direct(self):
        await self._sidebar_click(Section.MESSAGES)
        await self._wait_after(Section.MESSAGES)
        await self._medium()
        self._current = Section.MESSAGES

    async def go_search(self):
        await self._sidebar_click(Section.SEARCH)
        await self._wait_after(Section.SEARCH)
        await self._short()
        self._current = Section.SEARCH

    async def go_notifications(self):
        await self._sidebar_click(Section.NOTIFICATIONS)
        await self._wait_after(Section.NOTIFICATIONS)
        await self._short()
        self._current = Section.NOTIFICATIONS

    async def go_create(self):
        await self._sidebar_click(Section.CREATE)
        await self._wait_after(Section.CREATE)
        await self._short()
        self._current = Section.CREATE

    async def go_profile(self, username: str | None = None):
        user = username or self._username

        if not user or user == self._username:
            await self._profile_click()
        else:
            await self._nav(f"/{user}/")

        await self._wait_after(Section.PROFILE)
        await self._medium()
        self._current = Section.PROFILE


    async def go_to(self, section: Section, **kw):
        m = {
            Section.HOME:          self.go_home,
            Section.REELS:         self.go_reels,
            Section.EXPLORE:       self.go_explore,
            Section.MESSAGES:      self.go_direct,
            Section.SEARCH:        self.go_search,
            Section.NOTIFICATIONS: self.go_notifications,
            Section.CREATE:        self.go_create,
            Section.PROFILE:       lambda: self.go_profile(kw.get("username")),
        }
        fn = m.get(section)
        if fn:
            await fn()

    async def go_back(self):
        await self._page.go_back()
        await self._page.wait_for_load_state("domcontentloaded")
        await self._short()


    async def is_on(self, section: Section, timeout: int = 3000) -> bool:
        sel = _WAIT_AFTER.get(section)
        if not sel:
            return False
        try:
            await self._page.wait_for_selector(sel, timeout=timeout)
            return True
        except Exception:
            return False

    async def ensure_on(self, section: Section, **kw):
        if not await self.is_on(section):
            await self.go_to(section, **kw)


    async def _nav(self, path: str):
        url = f"https://www.instagram.com{path}"
        if self._page.url.rstrip("/") != url.rstrip("/"):
            await self._page.goto(url, wait_until="domcontentloaded")

    async def _wait_after(self, section: Section, timeout: int = 10_000):
        sel = _WAIT_AFTER.get(section)
        if sel:
            try:
                await self._page.wait_for_selector(sel, timeout=timeout)
            except Exception:
                pass

    async def _sidebar_click(self, section: Section):
        svg_sel = _SIDEBAR_SVG.get(section)
        if not svg_sel:
            return

        try:
            box = await self._page.evaluate(f"""
                () => {{
                    const svg = document.querySelector("{svg_sel}");
                    if (!svg) return null;
                    const a = svg.closest('a[role="link"]') || svg.closest('a');
                    if (!a) return null;
                    const r = a.getBoundingClientRect();
                    if (r.width === 0 || r.height === 0) return null;
                    return {{ x: r.x + r.width / 2, y: r.y + r.height / 2 }};
                }}
            """)
            if box:
                x = box["x"] + random.uniform(-3, 3)
                y = box["y"] + random.uniform(-3, 3)
                await self._page.mouse.click(x, y)
                await asyncio.sleep(0.8)
                return
        except Exception:
            pass

        try:
            anchor = await self._page.evaluate_handle(f"""
                () => {{
                    const svg = document.querySelector("{svg_sel}");
                    if (!svg) return null;
                    return svg.closest('a[role="link"]')
                        || svg.closest('a')
                        || svg.parentElement;
                }}
            """)
            el = anchor.as_element()
            if el:
                await el.dispatch_event("click")
                await asyncio.sleep(0.8)
                return
        except Exception:
            pass

        try:
            label = svg_sel.split("'")[1]  # извлекаем "Reels" из "svg[aria-label='Reels']"
            link = await self._page.query_selector(
                f"a[role='link']:has(svg[aria-label='{label}'])"
            )
            if link:
                await link.click(force=True)
                await asyncio.sleep(0.8)
                return
        except Exception:
            pass

        try:
            await self._page.evaluate(f"""
                () => {{
                    const svg = document.querySelector("{svg_sel}");
                    if (svg) {{
                        const a = svg.closest('a[role="link"]') || svg.closest('a');
                        if (a) a.click();
                        else svg.click();
                    }}
                }}
            """)
            await asyncio.sleep(0.8)
        except Exception:
            pass

    async def _profile_click(self):
        if self._username:
            try:
                box = await self._page.evaluate(f"""
                    () => {{
                        const a = document.querySelector('a[role="link"][href="/{self._username}/"]');
                        if (!a) return null;
                        const r = a.getBoundingClientRect();
                        if (r.width === 0) return null;
                        return {{ x: r.x + r.width / 2, y: r.y + r.height / 2 }};
                    }}
                """)
                if box:
                    await self._page.mouse.click(
                        box["x"] + random.uniform(-3, 3),
                        box["y"] + random.uniform(-3, 3)
                    )
                    await asyncio.sleep(0.8)
                    return
            except Exception:
                pass

        try:
            box = await self._page.evaluate("""
                () => {
                    const imgs = document.querySelectorAll('nav img[alt], div[role="navigation"] img[alt]');
                    for (const img of imgs) {
                        const a = img.closest('a[role="link"]');
                        if (a && a.getAttribute('href') && a.getAttribute('href') !== '#') {
                            const r = a.getBoundingClientRect();
                            if (r.width > 0 && r.y > 400) {  // внизу sidebar
                                return { x: r.x + r.width / 2, y: r.y + r.height / 2 };
                            }
                        }
                    }
                    return null;
                }
            """)
            if box:
                await self._page.mouse.click(
                    box["x"] + random.uniform(-3, 3),
                    box["y"] + random.uniform(-3, 3)
                )
                await asyncio.sleep(0.8)
                return
        except Exception:
            pass

        try:
            box = await self._page.evaluate("""
                () => {
                    const spans = document.querySelectorAll('a[role="link"] span');
                    for (const span of spans) {
                        if (span.textContent?.trim() === 'Profile') {
                            const a = span.closest('a[role="link"]');
                            if (a) {
                                const r = a.getBoundingClientRect();
                                if (r.width > 0) return { x: r.x + r.width / 2, y: r.y + r.height / 2 };
                            }
                        }
                    }
                    return null;
                }
            """)
            if box:
                await self._page.mouse.click(
                    box["x"] + random.uniform(-3, 3),
                    box["y"] + random.uniform(-3, 3)
                )
                await asyncio.sleep(0.8)
                return
        except Exception:
            pass

        if self._username:
            await self._nav(f"/{self._username}/")