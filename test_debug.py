from src.utils import load_json_config
from src.audio_classifier import classify_audio, _find_known_artist

cfg = load_json_config('config/classifier_config.json', {})
ka = cfg.get('known_artists', {})

# Test cek artis dari filename
for fn in ['Slank - Ku Tak Bisa.mp3', 'Metallica - Enter Sandman.mp3', 'Blackpink - How You Like That.mp3']:
    folder, match = _find_known_artist(fn, ka)
    print("File:", fn)
    print("  Artist found:", match, "->", folder)

    r = classify_audio(fn, '', '', '', 0.0, '', cfg)
    print("  Score:", r['confidence_score'], "| Decision:", r['decision'])
    for s in r['signals']:
        if s['strength'] != 'INFO':
            print("   ", s['source'], "+"+str(s['points']), s['value'])
    if r['warnings']:
        print("  Warnings:", r['warnings'])
    print()
