# DitheredNeoPixel
A class for getting a better colour range our of WS2812b LEDs

'''
>>> import board
>>> from DitheredNeopixel import *
>>> pixels = DitheredNeopixel(board.GP0, 5,4)
>>> pixels[1] = (100,100,100)
>>> pixels.start()
>>> 
'''
