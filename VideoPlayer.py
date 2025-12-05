import flet as ft
import cv2
import base64
import time
import asyncio
import numpy as np

class VideoPlayer(cv2.VideoCapture):
	instance = None

	def __new__(cls):
		if cls.instance is None:
			cls.instance = super().__new__(cls)
		return cls.instance
	
	def __init__(self):
		super().__init__()
		self.view = None

video_player = VideoPlayer()

class VideoView(ft.Container):
	VIEW_WIDTH = 256
	VIEW_HEIGHT = 144
	ARROW_SIZE = 48
	
	def __init__(self, _video_path, _thumbnail_path=None):
		super().__init__()
		self.path = _video_path

		self.width = VideoView.VIEW_WIDTH
		self.height = VideoView.VIEW_HEIGHT
		self.bgcolor = ft.Colors.GREY_200
		self.alignment = ft.alignment.center
		self.on_click = self.Play
		self.content = self.MakePlayIcon()
		

		if _thumbnail_path is not None:
			self.image = ft.DecorationImage(src=_thumbnail_path)

		self.frame_width = 0
		self.frame_height = 0
		self.frame_max = 0		# 合計フレーム数
		self.frame_pos = 0		# 何フレーム目か
		self.frames = 0			# 何フレーム描画したか
		self.fps = 0
		self.draw_start = 0		# 再生開始時間
		self.draw_end = 0		# 描画終了時間

		self.running = False

	def MakePlayIcon(self):
		# 再生アイコン
		return ft.Container(
			content=ft.Icon(ft.Icons.PLAY_ARROW_ROUNDED, color=ft.Colors.WHITE, size=48),
			width=50,
			height=50,
			border_radius=25,
			bgcolor=ft.Colors.BLACK87,
			alignment=ft.alignment.center,
			border = ft.border.all(width=2, color=ft.Colors.WHITE)
		)
	
	def will_unmount(self):
		self.running = False

	def Play(self, e):
		if video_player.view is not self:
			# 別の場所で再生中なら、Stopして、自身を再生開始
			if video_player.view is not None and video_player.view.running == True:
				video_player.view.Stop(e=None)
				time.sleep(0.1)	# 再生失敗することがあるからちょっと待つ

			video_player.view = self

		if video_player.open(self.path) == False:
			print('Fail File Open')
			return

		self.frame_width = video_player.get(cv2.CAP_PROP_FRAME_WIDTH)
		self.frame_height = video_player.get(cv2.CAP_PROP_FRAME_HEIGHT)

		rate = 1.0
		if self.frame_width > self.frame_height:
			rate = VideoView.VIEW_WIDTH / self.frame_width
		else:
			rate = VideoView.VIEW_HEIGHT / self.frame_height

		self.frame_width = int(self.frame_width * rate)
		self.frame_height = int(self.frame_height * rate)

		self.frame_max = video_player.get(cv2.CAP_PROP_FRAME_COUNT)
		self.frames = 0
		self.fps = video_player.get(cv2.CAP_PROP_FPS)
		video_player.set(cv2.CAP_PROP_POS_FRAMES, self.frame_pos)
		
		zero_array = np.zeros((int(self.frame_height), int(self.frame_width)), dtype=np.uint8)
		ret, image = cv2.imencode('.jpg', zero_array)
		encode_data = base64.b64encode(image)

		self.content = ft.Image(src_base64=encode_data.decode('ascii'))
		self.on_click = self.Stop
		self.update()

		self.draw_start = time.time()

		self.running = True
		self.page.run_task(self.DrawUpdate, video_player)

	def Stop(self, e):
		self.running = False
		self.frame_pos = video_player.get(cv2.CAP_PROP_POS_FRAMES)
		self.on_click = self.Play

	async def DrawUpdate(self, _video_player: VideoPlayer):
		while(self.running == True):
			if _video_player.view is not self:
				self.Stop(e=None)

			if self.frames >= self.frame_max:
				self.frame_pos = 0
				self.on_click = self.Play
				break

			if self.DrawFrame() == False:
				self.frame_pos = 0
				self.on_click = self.Play
				break

			self.draw_end = time.time()

			# フレームレート制御
			wait_time = self.frames / self.fps - (self.draw_end - self.draw_start)
			#wait_time = 0.001

			if wait_time > 0 and wait_time < 1:
				await asyncio.sleep(wait_time)

		self.running = False

	def DrawFrame(self):
		# frame取得
		ret, frame = video_player.read()
		if ret == False:
			return False

		# 画像に変換
		frame = cv2.resize(frame, (self.frame_width, self.frame_height))
		ret, image = cv2.imencode('.jpg', frame)
		encode_data = base64.b64encode(image)

		if type(self.content) is not ft.Image:
			self.content = ft.Image()

		# imageに貼り付け
		self.content.src_base64 = encode_data.decode('ascii')
		self.update()

		self.frames += 1

		return True