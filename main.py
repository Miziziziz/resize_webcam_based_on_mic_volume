import sys, pygame
import imageio as iio
import time

import sounddevice as sd
import numpy as np


pygame.init()

camera = iio.get_reader("<video0>")
meta = camera.get_meta_data()
delay = 1/meta["fps"]

video_size = meta['source_size']
screen_size = 1280 , 720
speed = [1, 1]
background_color = 0, 255, 0

max_vol = 40
cur_scale = 0.5
min_scale = 0.1
max_scale = 0.3
goal_scale = 1.0
scale_down_speed = 0.002
scale_up_speed = 0.01
last_volume_norm = 0
#camera.close()

position_left = 50
position_right = 50

crop_left = 200
crop_right = 200
crop_top = 100
crop_bottom = 100

def track_mic_volume(indata, frames, time, status):
   volume_norm = int(np.linalg.norm(indata) * 10)
   volume_norm = max(min(volume_norm, max_vol), 0)
   global last_volume_norm
   last_volume_norm = volume_norm

def update_scale():
    global cur_scale
    global goal_scale
    goal_scale = min(goal_scale, max_scale)
    goal_scale = max(goal_scale, min_scale)
    if cur_scale > min_scale and last_volume_norm < 6:
        cur_scale -= scale_down_speed
    if cur_scale < max_scale and last_volume_norm > 10:
        cur_scale += scale_up_speed * last_volume_norm / max_vol


audio_stream = sd.InputStream(callback=track_mic_volume)
audio_stream.start()
screen = pygame.display.set_mode(screen_size)

rect_position = (position_left, position_right, 0, 0)

while 1:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            camera.close()
            audio_stream.close()
            sys.exit()

    update_scale()

    raw_frame = pygame.surfarray.make_surface(camera.get_next_data())
    rotated_frame = pygame.transform.rotate(raw_frame, -90)


    scaled_to_screen_frame = pygame.transform.scale(rotated_frame, screen_size)

    cropped_size = (screen_size[0] - crop_left - crop_right, screen_size[1] - crop_top - crop_bottom)
    cropped_frame = pygame.Surface(cropped_size)
    cropped_frame.fill(background_color)
    cropped_frame.blit(scaled_to_screen_frame, (0, 0), (crop_left, crop_top, cropped_size[0] - crop_right, cropped_size[1] - crop_bottom))

    new_size = (int(float(cropped_size[0])*cur_scale), int(float(cropped_size[1])*cur_scale))
    frame = pygame.transform.scale(cropped_frame, new_size)

    screen.fill(background_color)
    screen.blit(frame, rect_position)
    pygame.display.flip()

    time.sleep(delay)
