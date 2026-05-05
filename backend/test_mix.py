from pedalboard import Mix, PitchShift, Pedalboard

try:
    m = Mix([PitchShift(12), PitchShift(-12), Pedalboard([])])
    print("Mix works!")
except Exception as e:
    print(f"Error: {e}")
