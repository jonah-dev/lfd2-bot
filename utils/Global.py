# Relevant constants can live here
class Constants:
    # Teams
    INFECTED = "Infected"
    SURVIVOR = "Survivor"

    def getTeamOptions(self):
        return [self.INFECTED, self.SURVIVOR]