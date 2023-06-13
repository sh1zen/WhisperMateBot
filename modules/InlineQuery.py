from html import escape
from uuid import uuid4

import requests
from telegram import InlineQueryResultGif, InputTextMessageContent, InlineQueryResultArticle
from telegram.ext import InlineQueryHandler, ContextTypes

from utils.ModuleBase import ModuleBase


class InlineQuery(ModuleBase):

    def register_handlers(self, keyboard=None):
        self.app.add_handler(InlineQueryHandler(self.handler))

    @staticmethod
    def sanitize_text(text, min_len=0):
        text = text.strip(' ')
        return text if (min_len and len(text)) >= min_len else ''

    def wikipedia_search(self, search_query, lang='en'):

        search_query = self.sanitize_text(search_query, 4)

        if not search_query:
            return []

        import wikipedia
        wikipedia.set_lang(lang)

        page_summary = wikipedia.summary(search_query, sentences=12)

        response = [
            InlineQueryResultArticle(
                id=str(uuid4()),
                title=f"Summary: {search_query}",
                input_message_content=InputTextMessageContent(page_summary.strip())
            )
        ]

        search_results = wikipedia.search(search_query, results=5, suggestion=False)

        for result in search_results:
            page = wikipedia.page(result)

            summary = page.summary[:300] + '...' if len(page.summary) > 300 else page.summary
            reply_text = f"<b>{page.title}</b>\n\n{summary}\n\nRead more: {page.url}"

            response.append(
                InlineQueryResultArticle(
                    id=str(uuid4()),
                    title=f"Wiki: {page.title}",
                    input_message_content=InputTextMessageContent(reply_text),
                )
            )

        return response

    async def search_gif(self, query):

        query = self.sanitize_text(query, 3)

        if not query:
            return []

        # Perform a search for GIFs using the Giphy API (replace YOUR_GIPHY_API_KEY with your actual API key)
        giphy_api_key = 'YOUR_GIPHY_API_KEY'
        response = requests.get(f'https://api.giphy.com/v1/gifs/search?api_key={giphy_api_key}&q={query}&limit=5')
        gifs = response.json().get('data', [])

        results = []
        for gif in gifs:
            gif_id = gif.get('id')
            gif_url = gif.get('images', {}).get('downsized_medium', {}).get('url')
            gif_title = gif.get('title')

            # Create an InlineQueryResultGif for each search result
            results.append(
                InlineQueryResultGif(
                    id=gif_id,
                    gif_url=gif_url,
                    thumb_url=gif_url,
                    caption=gif_title,
                    input_message_content=InputTextMessageContent(gif_title)
                )
            )

        # Send the search results back to the user
        return results

    async def handler(self, update, context: ContextTypes.DEFAULT_TYPE) -> None:

        query = update.inline_query.query.lower()

        if not self.sanitize_text(query, 3):
            return

        if query.startswith('wiki'):

            results = self.wikipedia_search(query.replace('wiki', ''), context.user_data.get('lang') or 'en')

        elif query.startswith('gif'):

            results = self.search_gif(query.replace('gif', ''))

        else:
            results = [
                InlineQueryResultArticle(
                    id=str(uuid4()),
                    title="Caps",
                    input_message_content=InputTextMessageContent(query.upper()),
                ),
                InlineQueryResultArticle(
                    id=str(uuid4()),
                    title="Bold",
                    input_message_content=InputTextMessageContent(
                        f"<b>{escape(query)}</b>"
                    ),
                ),
                InlineQueryResultArticle(
                    id=str(uuid4()),
                    title="Italic",
                    input_message_content=InputTextMessageContent(
                        f"<i>{escape(query)}</i>"
                    ),
                )
            ]

        await update.inline_query.answer(results)
