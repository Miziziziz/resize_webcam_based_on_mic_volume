import sys, pygame
import imageio as iio
import time

import sounddevice as sd
import numpy as np

from enum import Enum

class Anchors(Enum):
    TOP_LEFT = 1
    TOP_RIGHT = 2
    BOT_LEFT = 3
    BOT_RIGHT = 4
    MIDDLE = 5

cur_anchor = Anchors.BOT_RIGHT

pygame.init()

camera = iio.get_reader("<video0>")
meta = camera.get_meta_data()
delay = 1/meta["fps"]

video_size = meta['source_size']
screen_size = 1280 , 720
speed = [1, 1]
background_color = 0, 255, 0

max_vol = 40
cur_scale = 0.1
min_scale = 0.1
max_scale = 0.5
cur_scale = min_scale

goal_scale = 1.0
scale_down_speed = 0.1
scale_up_speed = 0.3
last_volume_norm = 0

margin_left = 50
margin_top = 50

# crop_left = 0
# crop_right = 0
# crop_top = 0
# crop_bottom = 0

crop_left = 300
crop_right = 300
crop_top = 150
crop_bottom = 150

time_before_shrink_size = 0.2
cur_time_before_shrink = 0.0

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

    global cur_time_before_shrink
    if cur_scale > min_scale and last_volume_norm < 10:
        if cur_time_before_shrink <= 0:
            cur_scale -= scale_down_speed
        else:
            cur_time_before_shrink -= delay
    if cur_scale < max_scale and last_volume_norm > 10:
        cur_scale += scale_up_speed * last_volume_norm / max_vol
        cur_time_before_shrink = time_before_shrink_size
    cur_scale = max(min(cur_scale, max_scale), min_scale)

def calculate_rect_position(size_x, size_y):
    scaled_right_crop = int(cur_scale * crop_right)
    scaled_bot_crop = int(cur_scale * crop_bottom)

    if cur_anchor == Anchors.TOP_LEFT:
        return (margin_left, margin_top, 0, 0)
    if cur_anchor == Anchors.TOP_RIGHT:
        return (screen_size[0] - size_x - margin_left + scaled_right_crop, margin_top, 0, 0)
    if cur_anchor == Anchors.BOT_LEFT:
        return (margin_left, screen_size[1] - size_y - margin_top + scaled_bot_crop, 0, 0)
    if cur_anchor == Anchors.BOT_RIGHT:
        return (screen_size[0] - size_x - margin_left + scaled_right_crop, screen_size[1] - size_y - margin_top + scaled_bot_crop, 0, 0)
    if cur_anchor == Anchors.MIDDLE:
        return (screen_size[0]/2 - size_x/2, screen_size[1]/2 - size_y/2, 0, 0)
    return (0, 0, 0, 0)

try:
    audio_stream = sd.InputStream(callback=track_mic_volume)
    audio_stream.start()
    screen = pygame.display.set_mode(screen_size)

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

        rect_position = calculate_rect_position(new_size[0], new_size[1])

        screen.fill(background_color)
        screen.blit(frame, rect_position)
        pygame.display.flip()

        time.sleep(delay)
except:
    camera.close()
    audio_stream.close()
    sys.exit()
