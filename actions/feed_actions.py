import asyncio
from playwright.async_api import Page


class FeedActions:

    def __init__(self, page: Page):
        self._page = page

    async def scroll_down(self, pixels: int = 700):
        await self._page.evaluate(f"window.scrollBy(0, {pixels})")
        await asyncio.sleep(0.6)

    async def scroll_up(self, pixels: int = 700):
        await self._page.evaluate(f"window.scrollBy(0, -{pixels})")
        await asyncio.sleep(0.6)

    async def scroll_to_top(self):
        await self._page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(0.4)

    async def scroll_n_times(self, times: int = 3, pixels: int = 700, pause: float = 0.8):
        for _ in range(times):
            await self.scroll_down(pixels)
            await asyncio.sleep(pause)

    # async def get_posts(self):
    #     return await self._page.query_selector_all("article")

    # async def get_post_count(self) -> int:
    #     return len(await self.get_posts())

    async def click_post(self, index: int = 0):
        posts = await self.get_posts()
        if index >= len(posts):
            raise IndexError(f"Post {index} not found, visible: {len(posts)}")
        link = await posts[index].query_selector("a[href*='/p/'], a[href*='/reel/']")
        if link:
            await link.click()
        else:
            img = await posts[index].query_selector("img[srcset], img[src]")
            if img:
                await img.click()
            else:
                await posts[index].click()
        await asyncio.sleep(1.0)

    async def close_post(self):
        await self._page.go_back()
        await asyncio.sleep(0.8)

    async def open_and_close_post(self, index: int = 0, view_time: float = 2.0):
        await self.click_post(index)
        await asyncio.sleep(view_time)
        await self.close_post()

    async def like_post(self, index: int = 0):
        posts = await self.get_posts()
        if index < len(posts):
            btn = await posts[index].query_selector(
                "div[role='button']:has(svg[aria-label='Like'])"
            )
            if btn:
                await btn.click()
                await asyncio.sleep(0.5)

    async def open_story(self, index: int = 0):
        stories = await self.get_stories()
        if index >= len(stories):
            raise IndexError(f"Story {index} not found, visible: {len(stories)}")
        await stories[index].dispatch_event("click")
        await asyncio.sleep(2.0)

    async def scroll_stories_right(self):
        btn = await self._page.query_selector("button[aria-label='Next']")
        if btn:
            await btn.click()
            await asyncio.sleep(0.5)

    async def refresh(self):
        await self._page.reload(wait_until="domcontentloaded")
        await asyncio.sleep(1.0)

    async def infinite_scroll(self, max_scrolls: int = 20, pause: float = 1.5) -> int:
        prev = 0
        for _ in range(max_scrolls):
            await self.scroll_down()
            await asyncio.sleep(pause)
            cur = await self.get_post_count()
            if cur == prev:
                break
            prev = cur
        return prev