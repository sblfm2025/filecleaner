from src.audio_classifier import classify_audio_file

tests = [
    ("Slank", {"filename": "Slank - Ku Tak Bisa.mp3", "artist_tag": "Slank", "title_tag": "Ku Tak Bisa", "genre_tag": "Rock", "duration_seconds": 240}),
    ("Metallica", {"filename": "Metallica - Enter Sandman.mp3", "artist_tag": "Metallica", "title_tag": "Enter Sandman", "duration_seconds": 330}),
    ("Dewa19 parent misleading", {"filename": "Dewa 19 - Kangen.mp3", "parent_folder": "Dangdut Campur", "duration_seconds": 240}),
    ("Bugis 2 sinyal", {"filename": "Elong Bugis - Mappideceng.mp3", "genre_tag": "Bugis", "duration_seconds": 200}),
    ("Blackpink no tag", {"filename": "Blackpink - How You Like That.mp3", "duration_seconds": 200}),
    ("Sholawat", {"filename": "Sholawat Nabi - Ya Rasulullah.mp3", "duration_seconds": 180}),
    ("Murottal", {"filename": "Murottal Surah Al-Fatihah.mp3", "duration_seconds": 120}),
]

for label, kwargs in tests:
    r = classify_audio_file(**kwargs)
    print(f"\n[{label}]")
    print(f"  Score={r['confidence_score']} | Decision={r['decision']} | media={r['media_type']}")
    print(f"  target={r['target_folder']}")
    print(f"  Signals: {r['signals']}")
    print(f"  Warnings: {r['warnings']}")
    print(f"  Conflicts: {r['conflicts']}")
