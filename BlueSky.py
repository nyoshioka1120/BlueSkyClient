import asyncio
import flet as ft
from atproto import Client

# フィードの親クラス
class Feed(ft.ListView):
    def __init__(self, client):
        super().__init__()
        self.client = client
        self.post_list = []
        self.color_list = [ft.Colors.GREY_200,ft.Colors.WHITE]
        self.color = 0

    def did_mount(self):
        self.running = True
        self.page.run_task(self.update_timeline)

    def will_unmount(self):
        self.running = False

    def create_container(self, text):
        content = ft.Text(text)
        color = self.color_list[self.color%2]
        self.color += 1

        return ft.Container(
            content=content,
            margin=0,
            padding=0,
            alignment=ft.alignment.top_left,
            bgcolor=color,
            width=500,
            height=content.height,
            border_radius=0,
        )

    async def update_timeline(self):
        print("update Feed")
        await asyncio.sleep(10)

# タイムラインフィード
class Feed_TimeLine(Feed):
    def __init__(self, client):
        super().__init__(client)

    async def update_timeline(self):
        while 1:
            # タイムライン取得
            # client.get_timeline()
            timeline = self.client.get_timeline()

            for feed in reversed(timeline.feed):
                if feed.post.cid in self.post_list:
                    continue

                display_name = feed.post.author.display_name
                id = feed.post.author.handle
                text = feed.post.record.text
                post = display_name + '(@' + id + ')\n' + text
                self.controls.insert(0, self.create_container(post))

                self.post_list.append(feed.post.cid)

            self.update()
            print("update Feed_TimeLine")
            await asyncio.sleep(10)


# 検索フィード
class Feed_SearchPosts(Feed):
    def __init__(self, client, word):
        super().__init__(client)
        self.client = client
        self.word = word
        self.post_list = []
        self.color_list = [ft.Colors.GREY_200,ft.Colors.WHITE]
        self.color = 0

    async def update_timeline(self):
        while 1:
            # 検索実行
            # client.app.bsky.feed.search_posts({"q":検索文字, "sort":ソート順, "limit":取得上限})
            timeline = self.client.app.bsky.feed.search_posts({"q":self.word, "sort":"top", "limit":25})

            for post in timeline.posts:
                if post.cid in self.post_list:
                    continue

                display_name = post.author.display_name
                id = post.author.handle
                text = post.record.text
                contents = display_name + '(@' + id + ')\n' + text
                self.controls.append(self.create_container(contents))

                self.post_list.append(post.cid)
                print(post.cid)

            self.update()
            print("update Feed_SearchPosts")
            await asyncio.sleep(10)


def main(page: ft.Page):
    # bluesky ログイン
    client = Client(base_url='https://bsky.social')
    client.login(login='UserID',password='password')

    # window設定
    page.title = "BlueSky Client"
    page.vertical_alignment = ft.MainAxisAlignment.START

    # ページ全体のレイアウト
    row = ft.Row()
    row.vertical_alignment = ft.CrossAxisAlignment.START

    # フィード用レイアウト
    list_feed = ft.ListView()
    list_feed.horizontal = True
    list_feed.height = page.height - 20
    list_feed.spacing = 10

    page.add(row) 

    # ポスト用テキストボックス
    txt_post = ft.TextField(multiline=True)

    # ポストボタンアクション
    def post(e):
        if txt_post.value == '':
            return
        
        # ポスト実行
        # client.send_post(str)
        # client.send_image(str, bytes)
        client.send_post(txt_post.value)
        txt_post.value=''
        page.update()

    # ポストボタン
    btn_post = ft.FilledButton(text="Post", on_click=post)


    # 検索用テキストボックス
    txt_search = ft.TextField(multiline=True)

    # 検索ボタンアクション
    def search(e):
        if txt_search.value == '':
            return
        
        feed = Feed_SearchPosts(client=client, word=txt_search.value)
        feed.height = page.height - 20
        feed.width = 500
        list_feed.controls.append(feed)
        list_feed.update()
        txt_search.value=''
        page.update()

    # 検索ボタン
    btn_search = ft.FilledButton(text="Search", on_click=search)


    column_post=ft.Column([txt_post, btn_post, txt_search, btn_search])
    row.controls.append(column_post)

    row.controls.append(list_feed)

    time_line = Feed_TimeLine(client=client)
    time_line.height = page.height - 20
    time_line.width = 500
    list_feed.controls.append(time_line)

    page.update()

ft.app(target=main)