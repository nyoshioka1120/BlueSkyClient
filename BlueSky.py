import asyncio
import flet as ft
from atproto import Client
from atproto import models
from atproto_client.exceptions import BadRequestError
import VideoPlayer as vp
import os

PATH = os.path.join(os.path.dirname(__file__), 'data')

agent = Client(base_url='https://bsky.social')
client = Client(base_url='https://bsky.social')

# フィードの親クラス
class Feed(ft.Column):
    WIDTH = 256

    def __init__(self):
        super().__init__()
        self.post_list = []
        self.color_list = [ft.Colors.GREY_200,ft.Colors.WHITE]
        self.color = 0
        self.width = Feed.WIDTH
        self.scroll = "auto"
        self.video_path = None

    def did_mount(self):
        self.running = True
        self.page.run_task(self.update_timeline)

    def will_unmount(self):
        self.running = False

    def create_post_view(self, text):
        content = ft.Text(text)
        color = self.color_list[self.color%2]
        self.color += 1

        return ft.Container(
            content=content,
            margin=0,
            padding=0,
            alignment=ft.alignment.top_left,
            bgcolor=color,
            width=Feed.WIDTH,
            height=content.height,
            border_radius=0,
        )
    
    def create_video_post_view(self, _did, _cid, _post, _thumbnail):
        video_path = os.path.join(PATH, _cid)

        if os.path.exists(video_path) == True:
            print('skip')
        else:
            param = models.ComAtprotoSyncGetBlob.Params(
                did=_did,
                cid=_cid
            )

            try:
                data = agent.com.atproto.sync.get_blob(params=param)
                with open(video_path, "wb") as f:
                    f.write(data)
            except BadRequestError as e:
                print("get_blob:ResponsError")
                return self.create_post_view(_post)

        text = ft.Text(_post)
        video_view = vp.VideoView(_video_path=video_path, _thumbnail_path=_thumbnail)

        color = self.color_list[self.color%2]
        self.color += 1

        content = ft.Column(controls=[text, video_view])

        return ft.Container(
            content=content,
            margin=0,
            padding=0,
            alignment=ft.alignment.top_left,
            bgcolor=color,
            width=Feed.WIDTH,
            height=content.height,
            border_radius=0,
        )

    def has_video(self, _record):
        if 'embed' in vars(_record):
            if _record.embed is not None and 'video' in vars(_record.embed):
                return True
            
        return False

    async def update_timeline(self):
        print("update Feed")
        await asyncio.sleep(10)

# タイムラインフィード
class Feed_TimeLine(Feed):
    def __init__(self):
        super().__init__()

    async def update_timeline(self):
        while 1:
            # タイムライン取得
            timeline = client.get_timeline()

            for feed in reversed(timeline.feed):
                if feed.post.cid in self.post_list:
                    continue

                display_name = feed.post.author.display_name
                id = feed.post.author.handle
                text = feed.post.record.text
                post = display_name + '(@' + id + ')\n' + text

                if self.has_video(feed.post.record):
                    self.controls.insert(
                        0,
                        self.create_video_post_view(
                            _cid=feed.post.record.embed.video.ref.link,
                            _did=feed.post.author.did,
                            _post=post,
                            _thumbnail=feed.post.embed.thumbnail,
                        )
                    )
                else:
                    self.controls.insert(0, self.create_post_view(post))

                self.post_list.append(feed.post.cid)

            self.update()
            print("update Feed_TimeLine")
            await asyncio.sleep(10)


# 検索フィード
class Feed_SearchPosts(Feed):
    def __init__(self, word):
        super().__init__()
        self.word = word
        self.post_list = []
        self.color_list = [ft.Colors.GREY_200,ft.Colors.WHITE]
        self.color = 0

    async def update_timeline(self):
        while 1:
            # 検索実行
            # client.app.bsky.feed.search_posts({"q":検索文字, "sort":ソート順, "limit":取得上限})
            # sort:top トップ（Xでいう話題） | sort:latest 最新
            timeline = client.app.bsky.feed.search_posts({"q":self.word, "sort":"latest", "limit":25})

            for post in timeline.posts:
                if post.cid in self.post_list:
                    continue

                display_name = post.author.display_name
                id = post.author.handle
                text = post.record.text
                contents = display_name + '(@' + id + ')\n' + text
                
                if self.has_video(post.record):
                    self.controls.insert(
                        0,
                        self.create_video_post_view(
                            _cid=post.record.embed.video.ref.link,
                            _did=post.author.did,
                            _post=contents,
                            _thumbnail=post.embed.thumbnail
                        )
                    )
                else:
                    self.controls.insert(0, self.create_post_view(contents))

                self.post_list.append(post.cid)

            self.update()
            print("update Feed_SearchPosts")
            await asyncio.sleep(10)


def main(page: ft.Page):
    if os.path.exists(PATH) is False:
        os.mkdir(PATH)

    # bluesky ログイン
    client.login(login='UserID',password='password')

    # window設定
    page.title = "BlueSky Client"
    page.vertical_alignment = ft.MainAxisAlignment.START

    # ページ全体のレイアウト
    row = ft.Row()
    row.vertical_alignment = ft.CrossAxisAlignment.START
    row.scroll = "auto"

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
        
        feed = Feed_SearchPosts(word=txt_search.value)
        feed.height = page.height - 20
        feed.width = Feed.WIDTH
        row.controls.append(feed)
        row.update()
        txt_search.value=''
        page.update()

    # 検索ボタン
    btn_search = ft.FilledButton(text="Search", on_click=search)

    column_post=ft.Column([txt_post, btn_post, txt_search, btn_search])
    row.controls.append(column_post)

    time_line = Feed_TimeLine()
    time_line.height = page.height - 20
    row.controls.append(time_line)

    page.update()

ft.app(target=main)