from dataclasses import dataclass


@dataclass
class BikeModel:
    name: str
    year_start: int
    year_end: int
    variant: str

    @property
    def display_name(self) -> str:
        return f"{self.name} ({self.year_start}-{self.year_end})"


MULTISTRADA_1260_ENDURO = BikeModel(
    name="Multistrada 1260 Enduro",
    year_start=2019,
    year_end=2021,
    variant="Enduro",
)

MULTISTRADA_1260 = BikeModel(
    name="Multistrada 1260",
    year_start=2018,
    year_end=2021,
    variant="Standard",
)
