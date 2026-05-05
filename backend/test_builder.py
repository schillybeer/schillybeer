from audio_engine import engine

chain = [{'effect': 'Phaser', 'rate_hz': 0.5}, {'effect': 'Delay', 'delay_seconds': 0.3, 'feedback': 0.6, 'mix': 0.5}, {'effect': 'Reverb', 'room_size': 0.8}, {'effect': 'PitchShift', 'semitones': -7}, {'effect': 'PitchShift', 'semitones': 7}]

engine.build_dynamic_board(chain)
print("Board contains:")
print(engine.board)
