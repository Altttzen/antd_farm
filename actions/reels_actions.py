import asyncio
from playwright.async_api import Page
import random


class ReelsActions:
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
        return False

    async def next_reel(self):
        btn = await self._page.query_selector("div[aria-label='Navigate to next Reel']")
        if btn:
            await btn.click()
            await asyncio.sleep(1.2)
        else:
            await self._swipe("up")
            await asyncio.sleep(1.2)

    async def previous_reel(self):
        btn = await self._page.query_selector("div[aria-label='Navigate to previous Reel']")
        if btn:
            await btn.click()
            await asyncio.sleep(1.2)
        else:
            await self._swipe("down")
            await asyncio.sleep(1.2)

    async def like(self):        
        await self._click_btn("Like")
    async def unlike(self):      
        await self._click_btn("Unlike")
    async def save(self):        
        await self._click_btn("Save")
    async def share(self):       
        await self._click_btn("Share")
    async def more_options(self):
        await self._click_btn("More")
    async def open_comments(self):
        await self._click_btn("Comment")
        await asyncio.sleep(2.5)

    async def pause(self):
        player = await self._page.query_selector("div[aria-label='Video player']")
        if player:
            await player.click()
            await asyncio.sleep(0.4)
        else:
            await self._page.evaluate("""
                () => {
                    const v = document.querySelector('video');
                    if (v) v.paused ? v.play() : v.pause();
                }
            """)

    async def resume(self): 
        await self.pause()

    async def toggle_audio(self):
        btn = await self._page.query_selector("button[aria-label='Toggle audio']")
        if btn:
            await btn.click()
            await asyncio.sleep(0.4)
        else:
            await self._page.evaluate("""
                () => {
                    const v = document.querySelector('video');
                    if (v) v.muted = !v.muted;
                }
            """)

    async def follow_author(self):
        btn = await self._page.query_selector("div[role='button']:has-text('Follow')")
        if btn:
            t = (await btn.inner_text()).strip()
            if t == "Follow":
                await btn.click()
                await asyncio.sleep(0.5)

    async def go_to_author(self):
        author_link = await self._page.evaluate("""
            () => {
                let links = Array.from(document.querySelectorAll('a[href]'));
                
                // Все ссылки вида /username/reels/ с текстом
                let authorLinks = links.filter(a => {
                    let href = a.getAttribute('href') || '';
                    let text = a.innerText?.trim();
                    let rect = a.getBoundingClientRect();
                    
                    let isReelsLink = /^\\/[^/]+\\/reels\\/$/.test(href);
                    let hasText = text && text.length > 0;
                    let isVisible = rect.width > 0 && rect.height > 0;
                    
                    return isReelsLink && hasText && isVisible;
                });
                
                if (authorLinks.length === 0) return null;
                
                // Центр экрана по вертикали
                let screenCenterY = window.innerHeight / 2;
                
                // Выбираем ссылку ближайшую к центру экрана
                let closest = authorLinks.reduce((prev, curr) => {
                    let prevRect = prev.getBoundingClientRect();
                    let currRect = curr.getBoundingClientRect();
                    
                    let prevCenterY = prevRect.top + prevRect.height / 2;
                    let currCenterY = currRect.top + currRect.height / 2;
                    
                    let prevDist = Math.abs(prevCenterY - screenCenterY);
                    let currDist = Math.abs(currCenterY - screenCenterY);
                    
                    return currDist < prevDist ? curr : prev;
                });
                
                return {
                    href: closest.getAttribute('href'),
                    text: closest.innerText.trim()
                };
            }
        """)
        
        if author_link:
            href = author_link['href']
            
            await self._page.goto(f"https://www.instagram.com{href}")
            await asyncio.sleep(2.0)
            return True
        
        return False

    async def go_to_audio(self):
        a = await self._page.query_selector("a[href*='/audio/'], a[href*='music']")
        if a:
            await a.click()
            await asyncio.sleep(1.0)

    async def like_and_next(self):
        await self.like()
        await asyncio.sleep(0.3)
        await self.next_reel()

    async def _swipe(self, direction: str = "up", duration_ms: int = 300):
        vp = self._page.viewport_size or {"width": 1280, "height": 800}
        cx = vp["width"] // 2
        if direction == "up":
            sy, ey = int(vp["height"] * 0.7), int(vp["height"] * 0.3)
        else:
            sy, ey = int(vp["height"] * 0.3), int(vp["height"] * 0.7)
        steps = max(duration_ms // 16, 5)
        await self._page.mouse.move(cx, sy)
        await self._page.mouse.down()
        for i in range(1, steps + 1):
            await self._page.mouse.move(cx, sy + (ey - sy) * i / steps)
            await asyncio.sleep(0.016)
        await self._page.mouse.up()
        await asyncio.sleep(0.6)

    async def add_comment(self, text: str):
        await self.open_comments()
        await asyncio.sleep(1.2)

        try:
            inp = await self._page.wait_for_selector(
                "input[placeholder='Add a comment…']",
                timeout=5000
            )
            
            await inp.click()
            await asyncio.sleep(0.8) 
            active_inp = await self._page.query_selector(
                "div[contenteditable='true'][role='textbox']"
            )

            if active_inp:
                for part in [text[i:i+7] for i in range(0, len(text), 7)]:
                    await active_inp.type(part)
                    await asyncio.sleep(0.03)
                await asyncio.sleep(0.3)
                await self._page.keyboard.press("Enter")
                await asyncio.sleep(1.5)
            else:
                await self._page.keyboard.type(text, delay=50)
                await asyncio.sleep(0.3)
                await self._page.keyboard.press("Enter")
                await asyncio.sleep(1.5)

        except Exception as e:
            print(f"Comment: {e}")

        await self._page.keyboard.press("Escape")
        await asyncio.sleep(0.3)

    async def like_comments(self, count: int = 5):
        await self.open_comments()
        await asyncio.sleep(1.5)

        liked = 0

        while liked < count:
            buttons_info = await self._page.evaluate("""
                () => {
                    let dialog = document.querySelector("[role='dialog']");
                    if (!dialog) return [];
                    
                    let btns = Array.from(dialog.querySelectorAll("div[role='button']"));
                    let likeBtns = btns.filter(btn =>
                        btn.querySelector("svg[aria-label='Like'], svg[aria-label='Нравится']")
                    );
                    
                    return likeBtns.map((btn, i) => {
                        let rect = btn.getBoundingClientRect();
                        return {
                            index: i,
                            x: rect.x + rect.width / 2,
                            y: rect.y + rect.height / 2,
                            visible: rect.width > 0 && rect.height > 0 && rect.top > 0,
                        };
                    });
                }
            """)

            visible = [b for b in buttons_info if b['visible']]

            if not visible:
                break

            if liked >= len(visible):
                await self._page.evaluate("""
                    () => {
                        let dialog = document.querySelector("[role='dialog']");
                        if (dialog) {
                            // Ищем скроллящийся контейнер внутри диалога
                            let scrollable = Array.from(dialog.querySelectorAll('*')).find(el =>
                                el.scrollHeight > el.clientHeight + 10
                            );
                            if (scrollable) scrollable.scrollBy(0, 300);
                        }
                    }
                """)
                await asyncio.sleep(1.5)
                continue

            btn = visible[liked]
            
            offset_x = random.uniform(-3, 3)
            offset_y = random.uniform(-3, 3)
            
            await self._page.mouse.move(btn['x'] + offset_x, btn['y'] + offset_y)
            await asyncio.sleep(random.uniform(0.3, 0.7))
            await self._page.mouse.click(btn['x'] + offset_x, btn['y'] + offset_y)
            
            liked += 1
            
            await asyncio.sleep(random.uniform(1.5, 3.0))

        return liked

    async def reply_to_comment(self, number, reply_text):
        await self.open_comments()
        reply_btns = await self._page.query_selector_all("div[role='button']")
        targets = []
        for btn in reply_btns:
            txt = (await btn.text_content() or "").strip().lower()
            if "reply" in txt or "ответить" in txt:
                targets.append(btn)
        if targets and number < len(targets):
            await targets[number].click()
            await asyncio.sleep(0.8)
            inp = await self._page.query_selector("div[contenteditable='true'][role='textbox']")
            if inp:
                for part in [reply_text[i:i+7] for i in range(0, len(reply_text), 7)]:
                    await inp.type(part)
                    await asyncio.sleep(0.03)
                await asyncio.sleep(0.3)
                await self._page.keyboard.press("Enter")
                await asyncio.sleep(1.2)
        else:
            print(f"Can't find reply button for comment {number}")
        await self._page.keyboard.press("Escape")
        await asyncio.sleep(0.4)

    async def repost(self):
        btn = await self._page.query_selector(
            "div[role='button']:has(svg[aria-label='Repost'])"
        )
        if not btn:
            btn = await self._page.query_selector(
                "div[role='button']:has(svg[title='Repost'])"
            )
        if btn:
            await btn.click()
            await asyncio.sleep(0.5)
            return True
        return False
    
    async def follow(self):
        buttons = await self._page.query_selector_all(
            "button, div[role='button']"
        )
        for btn in buttons:
            try:
                txt = (await btn.text_content() or "").strip().lower()
                if txt in ["follow", "follow back", "requested"]:
                    await btn.click()
                    await asyncio.sleep(0.9)
                    return True
            except Exception:
                continue
        btn2 = await self._page.query_selector("button:has-text('Follow')")
        if btn2:
            await btn2.click()
            await asyncio.sleep(0.9)
            return True
        return False

    async def follow_author(self):
        follow_btn = await self._page.query_selector(
            "button[aria-label='Follow'], button:has-text('Follow'), div[role='button']:has-text('Follow')"
        )
        if follow_btn:
            await follow_btn.click()
            await asyncio.sleep(1)
            return True
        return False