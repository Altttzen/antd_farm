import asyncio
from playwright.async_api import Page


class CommentActions:

    def __init__(self, page: Page):
        self._page = page

    _INPUT = "textarea[aria-label='Add a comment…']"

    async def _container(self):
        h = await self._page.evaluate_handle("""() => {
            for (const el of document.querySelectorAll('div, ul')) {
                const s = getComputedStyle(el);
                if (el.scrollHeight > el.clientHeight + 50 &&
                    (s.overflowY === 'auto' || s.overflowY === 'scroll') &&
                    el.clientHeight > 100 && el.clientHeight < 600)
                    return el;
            }
            return null;
        }""")
        return h.as_element() if h else None

    async def scroll_down(self, times: int = 1, pixels: int = 300):
        c = await self._container()
        for _ in range(times):
            if c:
                await self._page.evaluate("(el,px)=>el.scrollTop+=px", c, pixels)
            else:
                await self._page.evaluate(f"window.scrollBy(0,{pixels})")
            await asyncio.sleep(0.5)

    async def scroll_up(self, times: int = 1, pixels: int = 300):
        c = await self._container()
        for _ in range(times):
            if c:
                await self._page.evaluate("(el,px)=>el.scrollTop-=px", c, pixels)
            else:
                await self._page.evaluate(f"window.scrollBy(0,-{pixels})")
            await asyncio.sleep(0.5)

    async def get_comments(self):
        return await self._page.query_selector_all("ul > li:has(span[dir='auto'])")

    async def get_comment_count(self) -> int:
        return len(await self.get_comments())

    async def get_comment_text(self, index: int = 0) -> str:
        comments = await self.get_comments()
        if index >= len(comments):
            return ""
        span = await comments[index].query_selector("span[dir='auto']")
        return (await span.inner_text()).strip() if span else ""

    async def load_more(self):
        btn = await self._page.query_selector(
            "div[role='button']:has-text('View all'), "
            "div[role='button']:has-text('Load more'), "
            "button:has-text('View all'), button:has-text('+')"
        )
        if btn:
            await btn.click()
            await asyncio.sleep(1.0)

    async def load_all_comments(self, max_loads: int = 10, pause: float = 1.0) -> int:
        prev = 0
        for _ in range(max_loads):
            await self.scroll_down(times=2)
            await self.load_more()
            await asyncio.sleep(pause)
            cur = await self.get_comment_count()
            if cur == prev:
                break
            prev = cur
        return prev

    async def type_comment(self, text: str):
        inp = await self._page.wait_for_selector(self._INPUT, timeout=5000)
        await inp.click()
        await asyncio.sleep(0.2)
        await inp.fill(text)
        await asyncio.sleep(0.2)

    async def post_comment(self):
        await self._page.keyboard.press("Enter")
        await asyncio.sleep(1.0)

    async def write_and_post(self, text: str):
        await self.type_comment(text)
        await self.post_comment()

    async def like_comment(self, index: int = 0):
        comments = await self.get_comments()
        if index < len(comments):
            btn = await comments[index].query_selector(
                "div[role='button']:has(svg[aria-label='Like'])"
            )
            if btn:
                await btn.click()
                await asyncio.sleep(0.3)

    async def reply_to_comment(self, index: int, text: str):
        comments = await self.get_comments()
        if index < len(comments):
            r = await comments[index].query_selector(
                "div[role='button']:has-text('Reply'), button:has-text('Reply')"
            )
            if r:
                await r.click()
                await asyncio.sleep(0.5)
                await self.type_comment(text)
                await self.post_comment()

    async def like_multiple(self, indices: list[int]):
        for idx in indices:
            await self.like_comment(idx)

    async def read_and_comment(self, text: str, scroll_times: int = 2):
        await self.scroll_down(times=scroll_times)
        await self.write_and_post(text)