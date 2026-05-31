from src.utils import load_json_config
from src.audio_classifier import classify_audio

cfg = load_json_config('config/classifier_config.json', {})

tests = [
    # (label, filename, artist_tag, title_tag, genre_tag, duration, parent_folder)
    ("JINGLE PREFIX",    "JINGLE - Hits FM Pagi.mp3",        "",          "",              "",         15.0,  "siaran"),
    ("SLANK ARTIS",      "Slank - Ku Tak Bisa.mp3",          "Slank",     "Ku Tak Bisa",   "",         240.0, "Rock Indonesia"),
    ("METALLICA BARAT",  "Metallica - Enter Sandman.mp3",    "Metallica", "Enter Sandman", "",         330.0, ""),
    ("TRACK AMBIGU",     "Track 01.mp3",                     "",          "",              "",         180.0, ""),
    ("BUGIS KEYWORD",    "Mappideceng - Bugis Klasik.mp3",   "",          "",              "",         200.0, ""),
    ("LOVE REMIX LEMAH", "Love Song Remix.mp3",              "",          "",              "",         210.0, ""),
    ("BUMPER RESMI",     "BUMPER - News Pagi Program.mp3",   "",          "",              "",         8.0,   ""),
    ("BLACKPINK KPOP",   "Blackpink - Pink Venom.mp3",       "Blackpink", "Pink Venom",    "K-Pop",    200.0, ""),
    ("DANGDUT GENRE",    "Via Vallen - Sayang.mp3",          "Via Vallen","Sayang",        "Dangdut",  210.0, ""),
    ("UNKNOWN WAV",      "aud-00012.wav",                    "",          "",              "",         5.0,   ""),
]

print("=" * 90)
print(f"{'Label':<20} {'Decision':<22} {'Score':>5} {'Folder'}")
print("=" * 90)
for label, fn, art, ttl, genre, dur, parent in tests:
    r = classify_audio(fn, art, ttl, genre, dur, parent, cfg)
    print(f"{label:<20} {r['decision']:<22} {r['confidence_score']:>5.0f}  {r['target_folder']}")
print("=" * 90)
print("Test selesai!")
