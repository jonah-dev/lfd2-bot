from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import numpy
# #USED TO BE A RUNNER
# from repositories.UserRepository import UserRepository

# repo = UserRepository('louis.db')
# repo.registerUser("https://steamcommunity.com/profiles/76561198042291372/" ,147788154831634434)


#TODO Don't hardcode asset folder path
t1 = [
    'Player 1',
    'Player 2',
    'Player 3',
    'Player 4',
]
t2 = [
    'Player 5',
    'Player 6',
    'Player 7',
    'Player 8',
]
#'coach_small.jpg',
# survivors = [
#     'coach.jpg',
#     'ellis.jpeg',
#     'nick.png',
#     'rochelle.png'
# ]
survivors = [
    'coach_small.png',
    'ellis_small.jpeg',
    'nick_small.png',
    'rochelle_small.png'
]
composite = None
# t1, t2 = teams
im = Image.open("assets/lobby.png")
infected_image = Image.open('assets/infected_small.png')
draw = ImageDraw.Draw(im)
profilePos = (184, 171)
teamPos = (227, 180)
textPos = (255, 180)
textOffset = 42
teamOffset = (-72, -11)
textColor = '#e4e4e4'
font = ImageFont.truetype("assets/Futurot.ttf", 16)

for p in t1:
    draw.text(textPos, p, font=font, fill=(81, 81, 81, 255))
    survivor_image = Image.open('assets/' + survivors.pop())
    nextTeamPos = tuple(numpy.add(textPos, teamOffset))
    im.paste(survivor_image, nextTeamPos)
    textPos = (textPos[0], textPos[1] + textOffset)

for p in t2:
    draw.text(textPos, p, font=font, fill=(81, 81, 81, 255))
    nextTeamPos = tuple(numpy.add(textPos, teamOffset))
    im.paste(infected_image, nextTeamPos)
    textPos = (textPos[0], textPos[1] + textOffset)


im.save('testComposite.png')