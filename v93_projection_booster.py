from dataclasses import dataclass

@dataclass
class Projection:
    passing_yards: float
    rushing_yards: float
    receiving_yards: float
    fantasy_points: float
    confidence: int
    floor: float
    ceiling: float
    boom_probability: int
    bust_probability: int

class PredictionEngineV2:
    WEIGHTS={
        "last5":0.35,
        "season":0.20,
        "opponent":0.15,
        "snap":0.10,
        "usage":0.10,
        "redzone":0.05,
        "team_points":0.05
    }

    def weighted_value(self, context):
        return (
            context.get("last5",0)*self.WEIGHTS["last5"]+
            context.get("season",0)*self.WEIGHTS["season"]+
            context.get("opponent",0)*self.WEIGHTS["opponent"]+
            context.get("snap",0)*self.WEIGHTS["snap"]+
            context.get("usage",0)*self.WEIGHTS["usage"]+
            context.get("redzone",0)*self.WEIGHTS["redzone"]+
            context.get("team_points",0)*self.WEIGHTS["team_points"]
        )

    def project(self, context):
        yards=self.weighted_value(context)
        fp=yards/10
        return Projection(
            passing_yards=round(yards,1),
            rushing_yards=round(context.get("rush",0),1),
            receiving_yards=round(context.get("rec",0),1),
            fantasy_points=round(fp,2),
            confidence=min(95,max(40,int(context.get("games",5)*10))),
            floor=round(yards*0.9,1),
            ceiling=round(yards*1.15,1),
            boom_probability=min(90,int(fp*2)),
            bust_probability=max(5,35-int(fp))
        )
