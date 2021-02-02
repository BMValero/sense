LAB2INT = {
    "\"Drinking\" gesture": 0,
    "\"Sleeping\" gesture": 1,
    "Calling someone closer": 2,
    "Covering ears": 3,
    "Covering eyes": 4,
    "Dabbing": 5,
    "Doing nothing": 6,
    "Doing other things": 7,
    "Facepalming": 8,
    "No person visible": 9,
    "Nodding": 10,
    "Pointing left": 11,
    "Pointing right": 12,
    "Pointing to the camera": 13,
    "Putting finger to mouth": 14,
    "Rolling hand": 15,
    "Scratching": 16,
    "Shaking head": 17,
    "Showing the middle finger": 18,
    "Swiping down": 19,
    "Swiping down (with two hands)": 20,
    "Swiping left": 21,
    "Swiping right": 22,
    "Swiping up": 23,
    "Swiping up (with two hands)": 24,
    "Thumb down": 25,
    "Thumb up": 26,
    "Waving": 27,
    "Zooming in": 28,
    "Zooming out": 29
}

INT2LAB = {value: key for key, value in LAB2INT.items()}

LAB_THRESHOLDS = {
    "\"Drinking\" gesture": .2,
    "\"Sleeping\" gesture": .7,
    "Calling someone closer": .5,
    "Covering ears": .5,
    "Covering eyes": .5,
    "Dabbing": .5,
    "Facepalming": .5,
    "Nodding": .5,
    "Pointing left": .3,
    "Pointing right": .3,
    "Pointing to the camera": .5,
    "Putting finger to mouth": .5,
    "Rolling hand": .5,
    "Scratching": .5,
    "Shaking head": .5,
    "Showing the middle finger": .3,
    "Swiping down": .65,
    "Swiping down (with two hands)": .5,
    "Swiping left": .5,
    "Swiping right": .5,
    "Swiping up": .5,
    "Swiping up (with two hands)": .5,
    "Thumb down": .5,
    "Thumb up": .5,
    "Waving": .5,
    "Zooming in": .5,
    "Zooming out": .5
}
