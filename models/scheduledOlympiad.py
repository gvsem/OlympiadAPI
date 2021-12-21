import json

import numpy as np
from pydantic import BaseModel
from pydantic.utils import Optional


class Track(BaseModel):
    name: str = ''
    profile: str = ''
    subjects: list = []
    level: int = 0

    @staticmethod
    def load(data):
        return Track(**data)


class ScheduledOlympiad(BaseModel):

    name: str = ''
    site: Optional[str] = ''
    tracks: list[Track] = []
    no: int = 0
    year: int = 2022

    @staticmethod
    def load(data):
        return ScheduledOlympiad(**data)


class Schedule(BaseModel):
    olympiads: list[ScheduledOlympiad] = []

    @staticmethod
    def load(data):
        return Schedule(**data)

    def extractNames(self):
        names = []
        for o in self.olympiads:
            names.append(o.name)
        return names

    def replaceName(self, old, new):
        for o in range(len(self.olympiads)):
            if self.olympiads[o].name == old:
                self.olympiads[o].name = new

    def replaceProfile(self, old, new):
        for o in range(len(self.olympiads)):
            for t in range(len(self.olympiads[o].tracks)):
                if self.olympiads[o].tracks[t].profile == old:
                    self.olympiads[o].tracks[t].profile = new

    def replaceSubject(self, old, new):
        for o in range(len(self.olympiads)):
            for t in range(len(self.olympiads[o].tracks)):
                arr = np.array(self.olympiads[o].tracks[t].subjects)
                self.olympiads[o].tracks[t].subjects = list(np.where(arr == old, new, arr))

    def countTracks(self):
        c = 0
        for o in self.olympiads:
            c += len(o.tracks)
        return c




