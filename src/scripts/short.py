import moviepy.editor as mp
from numpy import random
import os
import datetime as dt
from tts import generate_tts
from subtitles import generate_subs
from reddit import get_hot_post_data
from utils import Info, Error, Except
from meta import generate_video_meta
import llm

OUT_WIDTH = 1080
COLOR = "\033[92m"
END = "\033[0m"

subs = [
    "stories",     
    "confessions",
    "TrueOffMyChest",
    "IAmA",
    "JustNoFamily",
    "AmITheAsshole",
    "Relationship_Advice",
    "LetsNotMeet",
    "TrueStory",
    "UnresolvedMysteries",
    "MaliciousCompliance"
]

REDDIT_DATA = get_hot_post_data(subs[random.randint(0, len(subs))])
NAME = dt.datetime.now().strftime("%m-%d-%Y_%H-%M-%S")

OUTPUT_DIR = os.environ["OUTPUT_DIR"] or "./"
VIDEO_INPUT_DIR = os.environ["VIDEO_INPUT_DIR"] or "./"

Info("Loading video")
videos = [f for f in os.listdir(VIDEO_INPUT_DIR) if os.path.isfile(os.path.join(VIDEO_INPUT_DIR, f))]
vid = mp.VideoFileClip(VIDEO_INPUT_DIR + videos[random.randint(0, len(videos))], audio=False)
(w, h) = vid.size

x1, x2 = (w - OUT_WIDTH)//2, (w + OUT_WIDTH)//2
y1, y2 = 0, h

Info("Generating audio")
audio_path = generate_tts(REDDIT_DATA["content"], NAME)
audio = mp.AudioFileClip(audio_path)
vid_form = ""
if audio.duration >= 60:
    Info("Audio is LONG - long form video")
    vid_form = "long"
else:
    vid_form = "short"
    Info("Audio is SHORT - short form video")

Info("Cropping video")
rand_segment = random.randint(0, vid.duration - audio.duration + 0.5)
short = vid.subclip(rand_segment, rand_segment + audio.duration + 0.5).crop(x1=x1, x2=x2, y1=y1, y2=y2)
short.audio = audio

Info("Generating text")
text_segmets = generate_subs(audio_path)["segments"]

Info("Making text clip")
clips = []
total_duration = 0
for segment in text_segmets:
    for word in segment["words"]:
        clip = mp.TextClip(txt=word["word"], fontsize=100, font="Obelix-Pro", color="white", stroke_width=5, stroke_color="black")
        clip.size = (w, clip.size[1])
        clip = clip.set_start(word["start"])
        clip = clip.set_position(("center", "center"))
        clips.append(clip.set_duration(word["end"] - word["start"]))
    print("---- Segment:" + str(segment["id"]))
    print("Start:   " + str(segment["start"]))
    print("End:     " + str(segment["end"]))
    print("Duration:" + str(segment["end"] - segment["start"]))
subs = mp.CompositeVideoClip(clips)

Info("Putting it all together")
out = mp.CompositeVideoClip([short, subs.set_position(("center", "center"))]).set_duration(short.duration)
out.write_videofile(OUTPUT_DIR + NAME + ".mp4", threads=16)

Info("Generating video meta")
vid_title = llm.generate_reddit_video_title(REDDIT_DATA["subreddit"], REDDIT_DATA["title"], REDDIT_DATA["content"])
vid_desc = llm.generate_reddit_video_description(REDDIT_DATA["subreddit"], REDDIT_DATA["title"], REDDIT_DATA["content"])
vid_tags_str = llm.generate_reddit_video_tags(REDDIT_DATA["subreddit"], REDDIT_DATA["title"], REDDIT_DATA["content"])
vid_tags = vid_tags_str.split(",")

Info("Saving video meta")
generate_video_meta(NAME, vid_form, out.duration, False, REDDIT_DATA["url"], vid_title, vid_desc, vid_tags)

Info("Done!")
print("File name:  ", NAME)
print("Title:      ", vid_title)
print("Description:", vid_desc)
print("Tags:       ", vid_tags_str)
print("Duration:   ", out.duration)
print("Post link:  ", REDDIT_DATA["url"])
print("file://///wsl.localhost/Ubuntu/home/vizn3r/dev/yt-automation/videos/output/" + NAME + ".mp4")