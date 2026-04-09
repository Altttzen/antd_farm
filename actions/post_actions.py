import asyncio
from playwright.async_api import Page


class PostActions:

    def __init__(self, page: Page):
        self._page = page

    async def _click_btn(self, label: str) -> bool:
        btn = await self._page.query_selector(
            f"div[role='button']:has(svg[aria-label='{label}'])"
        )
        if btn:
            await btn.click()
            await asyncio.sleep(0.4)
            return True
        svg = await self._page.query_selector(f"svg[aria-label='{label}']")
        if svg:
            p = await svg.evaluate_handle(
                "el => el.closest('div[role=\"button\"], span, button') || el.parentElement"
            )
            await p.as_element().click()
            await asyncio.sleep(0.4)
            return True
        return False

    async def like(self):
        await self._click_btn("Like")

    async def unlike(self):
        await self._click_btn("Unlike")

    async def toggle_like(self):
        if await self._page.query_selector("svg[aria-label='Unlike']"):
            await self.unlike()
        else:
            await self.like()

    async def double_tap_like(self):
        media = (
            await self._page.query_selector("video")
            or await self._page.query_selector("img[srcset]")
            or await self._page.query_selector("img[src]:not([alt*='profile'])")
        )
        if media:
            await media.dblclick()
            await asyncio.sleep(0.5)

    async def save(self):
        await self._click_btn("Save")

    async def unsave(self):
        await self._click_btn("Remove")

    async def share(self):
        await self._click_btn("Share")

    async def repost(self):
        await self._click_btn("Repost")

    async def more_options(self):
        await self._click_btn("More options")

    async def carousel_next(self):
        btn = await self._page.query_selector(
            "article button[aria-label='Next'], button[aria-label='Next']"
        )
        if btn:
            await btn.click()
            await asyncio.sleep(0.4)

    async def carousel_prev(self):
        btn = await self._page.query_selector(
            "article button[aria-label='Go back'], article button[aria-label='Previous']"
        )
        if btn:
            await btn.click()
            await asyncio.sleep(0.4)

    async def browse_carousel(self, slides: int = 5):
        for _ in range(slides):
            await self.carousel_next()

    async def browse_carousel_back(self, slides: int = 5):
        for _ in range(slides):
            await self.carousel_prev()

    async def open_comments(self):
        await self._click_btn("Comment")

    async def toggle_audio(self):
        btn = await self._page.query_selector("button[aria-label='Toggle audio']")
        if btn:
            await btn.click()
            await asyncio.sleep(0.3)

    async def close(self):
        await self._page.go_back()
        await asyncio.sleep(0.8)

    async def get_author(self) -> str:
        el = await self._page.query_selector("a[role='link'] span[dir='auto']")
        if el:
            return (await el.inner_text()).strip()
        el = await self._page.query_selector("article header a[role='link']")
        return (await el.inner_text()).strip() if el else ""

    async def get_caption(self) -> str:
        spans = await self._page.query_selector_all("span[dir='auto']")
        for s in spans:
            text = await s.inner_text()
            if len(text) > 20:
                return text.strip()
        return ""

    async def get_likes_count(self) -> str:
        el = await self._page.query_selector(
            "div[role='button']:has-text('likes'), "
            "div[role='button']:has-text('like'), "
            "a[href*='liked_by'] span"
        )
        return (await el.inner_text()).strip() if el else "0"

    async def go_to_author(self):
        el = await self._page.query_selector("article header a[role='link']")
        if el:
            await el.click()
            await asyncio.sleep(1.0)

    async def like_and_save(self):
        await self.like()
        await self.save()

    async def view_full(self, carousel_slides: int = 0, read_time: float = 2.0):
        if carousel_slides:
            await self.browse_carousel(carousel_slides)
        await asyncio.sleep(read_time)