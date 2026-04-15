# feed_actions.py
import asyncio
from playwright.async_api import Page


class FeedActions:

    LABELS = {
        "like":           ["Нравится", "Like"],
        "unlike":         ["Не нравится", "Unlike"],
        "comment":        ["Комментировать", "Comment"],
        "repost":         ["Репостнуть", "Repost"],
        "share":          ["Поделиться", "Share"],
        "save":           ["Сохранить", "Save"],
        "unsave":         ["Удалить из сохранённых", "Remove"],
        "more":           ["Ещё", "More options"],
        # Сторис
        "like_story":     ["Нравится", "Like"],
        "next_story":     ["Далее", "Next"],
        "prev_story":     ["Назад", "Previous", "Back"],
        "play":           ["Воспроизвести", "Play"],
        "pause":          ["Пауза", "Pause"],
        "mute":           ["Звук выключен", "Audio is muted", "Mute"],
        "menu":           ["Меню", "Menu"],
        "close":          ["Закрыть", "Close"],
    }

    def __init__(self, page: Page):
        self._page = page


    async def _click_svg_btn(self, *labels: str, scope=None) -> bool:
        if scope is None:
            scope = self._page

        for label in labels:
            btn = await scope.query_selector(
                f"div[role='button']:has(svg[aria-label='{label}'])"
            )
            if btn:
                try:
                    await btn.scroll_into_view_if_needed()
                    await asyncio.sleep(0.3)
                    await btn.click()
                    await asyncio.sleep(0.6)
                    return True
                except Exception as e:
                    print(f"div click error: {e}")

            span = await scope.query_selector(
                f"span:has(svg[aria-label='{label}'])"
            )
            if span:
                try:
                    await span.scroll_into_view_if_needed()
                    await asyncio.sleep(0.3)
                    await span.click()
                    await asyncio.sleep(0.6)
                    return True
                except Exception as e:
                    print(f"span click error: {e}")

            svg = await scope.query_selector(f"svg[aria-label='{label}']")
            if svg:
                try:
                    parent = await svg.evaluate_handle("""el => {
                        let p = el.parentElement;
                        for (let i = 0; i < 5; i++) {
                            if (!p) break;
                            const role = p.getAttribute('role');
                            const tag = p.tagName.toLowerCase();
                            if (role === 'button' || tag === 'button') return p;
                            p = p.parentElement;
                        }
                        return el.parentElement;
                    }""")
                    el = parent.as_element()
                    if el:
                        await el.scroll_into_view_if_needed()
                        await asyncio.sleep(0.3)
                        await el.click()
                        await asyncio.sleep(0.6)
                        return True
                except Exception as e:
                    print(f"svgparent click error: {e}")

        return False

    async def _get_articles(self):
        return await self._page.query_selector_all("article")

    async def get_articles(self):
        return await self._get_articles()

    async def _get_center_article(self):
        try:
            await self._page.wait_for_selector("article", timeout=5000)
        except Exception:
            return None

        idx = await self._page.evaluate("""() => {
            const arts = Array.from(document.querySelectorAll('article'));
            if (!arts.length) return 0;
            const cy = window.innerHeight / 2;
            let best = 0, bestDist = Infinity;
            arts.forEach((a, i) => {
                const r = a.getBoundingClientRect();
                const dist = Math.abs((r.top + r.height / 2) - cy);
                if (dist < bestDist) { bestDist = dist; best = i; }
            });
            return best;
        }""")
        arts = await self._get_articles()
        return arts[idx] if idx < len(arts) else None

    async def _scroll_into_center(self, article):
        await article.evaluate(
            "el => el.scrollIntoView({behavior:'smooth', block:'center'})"
        )
        await asyncio.sleep(1.2)


    async def scroll_down(self, pixels: int = 700):
        await self._page.evaluate(
            f"window.scrollBy({{top:{pixels}, behavior:'smooth'}})"
        )
        await asyncio.sleep(1.0)

    async def scroll_up(self, pixels: int = 700):
        await self._page.evaluate(
            f"window.scrollBy({{top:-{pixels}, behavior:'smooth'}})"
        )
        await asyncio.sleep(1.0)

    async def scroll_feed(self, steps: int = 5,
                          pixels_per_step: int = 700,
                          delay: float = 1.5):
        for i in range(steps):
            await self.scroll_down(pixels_per_step)
            await asyncio.sleep(delay)

    async def scroll_to_top(self):
        await self._page.evaluate("window.scrollTo(0,0)")
        await asyncio.sleep(1.0)

    async def like_post(self, article=None) -> bool:
        if article is None:
            article = await self._get_center_article()
        if article is None:
            return False
        await self._scroll_into_center(article)
        result = await self._click_svg_btn(*self.LABELS["like"], scope=article)
        return result

    async def unlike_post(self, article=None) -> bool:
        if article is None:
            article = await self._get_center_article()
        if article is None:
            return False
        await self._scroll_into_center(article)
        result = await self._click_svg_btn(*self.LABELS["unlike"], scope=article)
        return result


    async def comment_post(self, text: str, article=None) -> bool:
        try:
            comment_btn = self._page.locator("svg[aria-label='Comment']").first
            await comment_btn.click()
            await asyncio.sleep(2.0)

            textarea = self._page.locator(
                "textarea[placeholder='Add a comment…'], "
                "textarea[aria-label='Add a comment…']"
            ).first
            await textarea.wait_for(state="visible", timeout=5000)
            await textarea.click()
            await asyncio.sleep(0.3)
            await self._page.keyboard.type(text, delay=50)
            await asyncio.sleep(0.8)
            post_btn = self._page.locator("div[role='button']:has-text('Post')").last
            await post_btn.wait_for(state="visible", timeout=5000)
            
            try:
                await post_btn.click(force=True)
            except:
                await post_btn.dispatch_event("click")
            
            await asyncio.sleep(2.0)
            await self._page.keyboard.press("Escape")
            await asyncio.sleep(1.0)
            return True

        except Exception as e:
            print(f"comment_post ошибка: {e}")
            try:
                await self._page.keyboard.press("Escape")
            except:
                pass
            return False

    async def like_comment(self, comment_index: int = 0) -> bool:
        try:
            # height="12" — это лайки комментариев (не поста)
            like_btns = self._page.locator("svg[aria-label='Like'][height='12']")
            count = await like_btns.count()

            if count == 0:
                return False

            target = like_btns.nth(comment_index)
            await target.wait_for(state="visible", timeout=3000)

            try:
                await target.click(force=True)
            except:
                await target.dispatch_event("click")

            await asyncio.sleep(1.0)
            return True

        except Exception as e:
            return False


    async def reply_to_comment(self, text: str, comment_index: int = 0) -> bool:
        try:
            reply_spans = self._page.locator(
                "span.x193iq5w:has-text('Reply')"
            )
            count = await reply_spans.count()
            if count == 0:
                return False

            target = reply_spans.nth(comment_index)
            await target.wait_for(state="visible", timeout=3000)

            try:
                await target.click(force=True)
            except:
                await target.dispatch_event("click")

            await asyncio.sleep(1.0)
            textarea = self._page.locator(
                "textarea[placeholder='Add a comment…'],"
                "textarea[aria-label='Add a comment…']"
            ).first
            await textarea.wait_for(state="visible", timeout=5000)
            await textarea.click()
            await asyncio.sleep(0.3)
            await self._page.keyboard.type(text, delay=50)
            await asyncio.sleep(0.8)
            post_btn = self._page.locator("div[role='button']:has-text('Post')").last
            await post_btn.wait_for(state="visible", timeout=5000)

            try:
                await post_btn.click(force=True)
            except:
                await post_btn.dispatch_event("click")

            await asyncio.sleep(2.0)
            return True

        except Exception as e:
            return False

    async def repost_post(self, article=None) -> bool:
        if article is None:
            article = await self._get_center_article()
        if article is None:
            return False
        await self._scroll_into_center(article)
        result = await self._click_svg_btn(*self.LABELS["repost"], scope=article)
        return result

    async def share_post(self, article=None) -> bool:
        if article is None:
            article = await self._get_center_article()
        if article is None:
            return False
        await self._scroll_into_center(article)
        result = await self._click_svg_btn(*self.LABELS["share"], scope=article)
        return result

    async def share_to_first(self, article=None) -> bool:
        opened = await self.share_post(article)
        if not opened:
            return False
        await asyncio.sleep(2.5)

        recipient = await self._page.query_selector(
            "button[name='send'], "
            "div[role='button']:has(img[alt*='profile']), "
            "div[role='button']:has(img[alt*='Profile'])"
        )
        if recipient:
            await recipient.click()
            await asyncio.sleep(0.8)

        send_btn = (
            await self._page.query_selector("div[role='button']:has-text('Send')")
            or await self._page.query_selector("button:has-text('Send')")
        )
        if send_btn:
            await send_btn.click()
            await asyncio.sleep(1.0)
            return True

        await self._page.keyboard.press("Escape")
        return False

    async def more_options_post(self, article=None) -> bool:
        if article is None:
            article = await self._get_center_article()
        if article is None:
            return False
        await self._scroll_into_center(article)
        result = await self._click_svg_btn(*self.LABELS["more"], scope=article)
        return result

    async def _click_by_svg_label(self, *labels: str) -> bool:
        for label in labels:
            btn = await self._page.query_selector(
                f"button[aria-label='{label}']"
            )
            if btn:
                try:
                    await btn.evaluate("el => el.click()")
                    await asyncio.sleep(0.6)
                    return True
                except Exception as e:
                    print(e)

        for label in labels:
            svg = await self._page.query_selector(f"svg[aria-label='{label}']")
            if not svg:
                continue
            try:
                parent = await svg.evaluate_handle("""el => {
                    let p = el.parentElement;
                    for (let i = 0; i < 8; i++) {
                        if (!p) break;
                        const role = p.getAttribute('role');
                        const tag  = p.tagName.toLowerCase();
                        if (role === 'button' || tag === 'button') return p;
                        p = p.parentElement;
                    }
                    return el.parentElement;
                }""")
                el = parent.as_element()
                if el:
                    await el.evaluate("e => e.click()")
                    await asyncio.sleep(0.6)
                    print(f"svg parent click '{label}'")
                    return True
            except Exception as e:
                print(f"svg parent '{label}': {e}")

        return False

    async def get_stories_list(self):
        items = await self._page.query_selector_all(
            "div[role='button'][aria-label*='Story by']"
        )
        return items

    async def _click_story_element(self, element) -> bool:
        try:
            span = await element.query_selector("span[role='link']")
            if span:
                await span.evaluate("el => el.click()")
                await asyncio.sleep(3.0)
                if await self._is_story_open():
                    return True
        except Exception as e:
            print(f"span JS click: {e}")
        try:
            await element.evaluate("el => el.click()")
            await asyncio.sleep(3.0)
            if await self._is_story_open():
                return True
        except Exception as e:
            print(f"div JS click: {e}")
        return False

    async def open_first_story(self) -> bool:
        stories = await self.get_stories_list()
        if not stories:
            return False
        return await self._click_story_element(stories[0])

    async def open_story_by_index(self, index: int = 0) -> bool:
        stories = await self.get_stories_list()
        if index < len(stories):
            return await self._click_story_element(stories[index])
        return False

    async def like_story(self) -> bool:
        svgs = await self._page.query_selector_all("svg[aria-label='Like']")
        if not svgs:
            return False

        svg = svgs[-1]
        try:
            parent = await svg.evaluate_handle("""el => {
                let p = el.parentElement;
                for (let i = 0; i < 8; i++) {
                    if (!p) break;
                    const role = p.getAttribute('role');
                    const tag  = p.tagName.toLowerCase();
                    if (role === 'button' || tag === 'button') return p;
                    p = p.parentElement;
                }
                return el.parentElement;
            }""")
            el = parent.as_element()
            if el:
                await el.evaluate("e => e.click()")
                await asyncio.sleep(0.8)
                return True
        except Exception as e:
            print(f"like_story: {e}")

        return False

    async def next_story(self) -> bool:
        btn = await self._page.query_selector(
            "div[role='button']:has(svg[aria-label='Next'])"
        )
        if btn:
            await btn.evaluate("el => el.click()")
            await asyncio.sleep(1.5)
            return True
        vp = self._page.viewport_size
        if vp:
            await self._page.mouse.click(
                int(vp['width'] * 0.85),
                int(vp['height'] * 0.5)
            )
            await asyncio.sleep(1.5)
            return True
        return False

    async def prev_story(self) -> bool:
        btn = await self._page.query_selector(
            "div[role='button']:has(svg[aria-label='Previous'])"
        )
        if btn:
            await btn.evaluate("el => el.click()")
            await asyncio.sleep(1.5)
            return True
        vp = self._page.viewport_size
        if vp:
            await self._page.mouse.click(
                int(vp['width'] * 0.15),
                int(vp['height'] * 0.5)
            )
            await asyncio.sleep(1.5)
            return True
        return False


    async def pause_story(self) -> bool:
        return await self._click_by_svg_label("Pause", "Пауза")

    async def play_story(self) -> bool:
        return await self._click_by_svg_label("Play", "Воспроизвести")

    async def toggle_audio_story(self) -> bool:
        svgs = await self._page.query_selector_all(
            "svg[aria-label='Audio is muted'], "
            "svg[aria-label='Audio is on']"
        )
        if svgs:
            svg = svgs[-1]
            try:
                parent = await svg.evaluate_handle("""el => {
                    let p = el.parentElement;
                    for (let i = 0; i < 8; i++) {
                        if (!p) break;
                        const role = p.getAttribute('role');
                        const tag  = p.tagName.toLowerCase();
                        if (role === 'button' || tag === 'button') return p;
                        p = p.parentElement;
                    }
                    return el.parentElement;
                }""")
                el = parent.as_element()
                if el:
                    await el.evaluate("e => e.click()")
                    await asyncio.sleep(0.5)
                    return True
            except Exception as e:
                print(f"toggle_audio: {e}")
        return False


    async def close_story(self) -> bool:
        btn = await self._page.query_selector("button[aria-label='Close']")
        if btn:
            await btn.evaluate("el => el.click()")
            await asyncio.sleep(1.0)
            return True

        result = await self._click_by_svg_label("Close", "Закрыть")
        if result:
            await asyncio.sleep(1.0)
            return True

        await self._page.keyboard.press("Escape")
        await asyncio.sleep(1.0)
        return True

    async def reply_to_story(self, text: str) -> bool:
        textarea = await self._page.query_selector(
            "textarea[placeholder*='Reply to'], "
            "textarea[placeholder*='Ответьте']"
        )
        if not textarea:
            return False

        await textarea.evaluate("el => el.click()")
        await asyncio.sleep(0.4)
        await textarea.fill("")
        await textarea.type(text, delay=60)
        await asyncio.sleep(0.5)

        send = await self._page.query_selector(
            "div[role='button']:has-text('Send'), "
            "button:has-text('Send'), "
            "div[role='button']:has-text('Отправить')"
        )
        if send:
            await send.evaluate("el => el.click()")
        else:
            await self._page.keyboard.press("Enter")

        await asyncio.sleep(1.0)
        return True

    async def react_to_story(self, emoji: str = "🔥") -> bool:
        btns = await self._page.query_selector_all(
            "div[role='button']:has(span.xcg35fi)"
        )
        if not btns:
            btns = await self._page.query_selector_all(
                "div[role='button'] > span[class*='xcg35fi']"
            )
        for btn in btns:
            span = await btn.query_selector("span[class*='xcg35fi'], span")
            if span:
                text = (await span.inner_text()).strip()
                if text == emoji:
                    await btn.evaluate("el => el.click()")
                    await asyncio.sleep(0.8)
                    return True
        return False

    async def browse_stories(self, count: int = 5, delay: float = 2.5):
        for i in range(count):
            ok = await self.next_story()
            await asyncio.sleep(delay)

    async def scroll_stories_tray(self, direction: str = "right") -> bool:
        tray = await self._page.query_selector(
            "ul:has(div[role='button'][aria-label*='Story by'])"
        )
        if tray:
            delta = 400 if direction == "right" else -400
            await self._page.evaluate(f"el => el.scrollBy({delta}, 0)", tray)
            await asyncio.sleep(0.5)
            return True
        stories = await self.get_stories_list()
        if stories:
            box = await stories[0].bounding_box()
            if box:
                await self._page.mouse.move(
                    box['x'] + box['width'] / 2,
                    box['y'] + box['height'] / 2
                )
                delta = -400 if direction == "right" else 400
                await self._page.mouse.wheel(delta, 0)
                await asyncio.sleep(0.5)
                return True
        return False
