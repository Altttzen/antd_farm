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


_NAV_SVG = {
    Section.SEARCH:        "svg[aria-label='Search']",
    Section.NOTIFICATIONS: "svg[aria-label='Notifications']",
    Section.CREATE:        "svg[aria-label='New post']",
}

_WAIT = {
    Section.HOME:     "article, div[role='button'][aria-label*='Story by']",
    Section.REELS:    "div[aria-label='Video player'], video",
    Section.MESSAGES: "div[aria-label='Thread list'], input[name='searchInput']",
    Section.EXPLORE:  "a[href*='/p/'], a[href*='/reel/']",
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
        await self._nav("/")
        await self._wait_for(Section.HOME)
        await self._medium()
        self._current = Section.HOME

    async def go_reels(self):
        await self._nav("/reels/")
        await self._wait_for(Section.REELS)
        await self._medium()
        self._current = Section.REELS

    async def go_explore(self):
        await self._nav("/explore/")
        await self._wait_for(Section.EXPLORE)
        await self._medium()
        self._current = Section.EXPLORE

    async def go_profile(self, username: str | None = None):
        user = username or self._username
        if user:
            await self._nav(f"/{user}/")
        else:
            img = await self._page.query_selector(
                "img[data-testid='user-avatar'], a[role='link'] img[alt*='profile']"
            )
            if img:
                p = await img.evaluate_handle("el => el.closest('a') || el")
                await p.as_element().click()
        await self._page.wait_for_load_state("domcontentloaded")
        await self._medium()
        self._current = Section.PROFILE

    async def go_direct(self):
        await self._nav("/direct/inbox/")
        await self._wait_for(Section.MESSAGES)
        await self._medium()
        self._current = Section.MESSAGES


    async def go_search(self):
        await self._sidebar_click(Section.SEARCH)
        try:
            await self._page.wait_for_selector(
                "input[aria-label='Search input']", timeout=5000
            )
        except Exception:
            pass
        await self._short()
        self._current = Section.SEARCH

    async def go_notifications(self):
        await self._sidebar_click(Section.NOTIFICATIONS)
        await self._medium()
        self._current = Section.NOTIFICATIONS

    async def go_create(self):
        await self._sidebar_click(Section.CREATE)
        try:
            await self._page.wait_for_selector(
                "div[role='dialog'], input[type='file']", timeout=5000
            )
        except Exception:
            pass
        await self._short()
        self._current = Section.CREATE


    async def go_to(self, section: Section, **kw):
        m = {
            Section.HOME:          self.go_home,
            Section.REELS:         self.go_reels,
            Section.EXPLORE:       self.go_explore,
            Section.PROFILE:       lambda: self.go_profile(kw.get("username")),
            Section.MESSAGES:      self.go_direct,
            Section.NOTIFICATIONS: self.go_notifications,
            Section.CREATE:        self.go_create,
            Section.SEARCH:        self.go_search,
        }
        fn = m.get(section)
        if fn:
            await fn()

    async def go_back(self):
        await self._page.go_back()
        await self._page.wait_for_load_state("domcontentloaded")
        await self._short()


    async def is_on(self, section: Section, timeout: int = 3000) -> bool:
        sel = _WAIT.get(section)
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

    async def _wait_for(self, section: Section, timeout: int = 10_000):
        sel = _WAIT.get(section)
        if sel:
            try:
                await self._page.wait_for_selector(sel, timeout=timeout)
            except Exception:
                pass

    async def _sidebar_click(self, section: Section):
        svg_sel = _NAV_SVG.get(section)
        if not svg_sel:
            return

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
                await asyncio.sleep(0.5)
                return
        except Exception:
            pass

        try:
            svg = await self._page.query_selector(svg_sel)
            if svg:
                await svg.dispatch_event("click")
                await asyncio.sleep(0.5)
                return
        except Exception:
            pass

        try:
            label_text = {
                Section.SEARCH: "Search",
                Section.NOTIFICATIONS: "Notifications",
                Section.CREATE: "New post",
            }.get(section, "")
            if label_text:
                link = await self._page.query_selector(
                    f"a[role='link']:has(svg[aria-label='{label_text}'])"
                )
                if link:
                    await link.dispatch_event("click")
                    await asyncio.sleep(0.5)
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
            await asyncio.sleep(0.5)
        except Exception:
            pass