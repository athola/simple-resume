import os
import pathlib
import yaml

from pydantic import BaseModel, validator, root_validator
from tqdm import tqdm
from typing import Literal, Union, Optional
from vpalette import get_colors
from vpalette.colors import COLORS

from image_transformations import (
    get_image,
    remove_bg,
    to_grayscale,
    add_background_color,
    round_image,
)

PATH_JOBS = pathlib.Path(__file__).parent.parent / "cv_private" / "utils_jobs"


class RemoveBg(BaseModel):
    action: Literal["remove_bg"]
    suffix: str = "_no_bg"
    alpha_matting: bool = True
    alpha_matting_foreground_threshold: int = 240
    alpha_matting_background_threshold: int = 10
    alpha_matting_erode_size: int = 40

    def run(self, image_in):
        return remove_bg(
            image_in,
            alpha_matting=self.alpha_matting,
            alpha_matting_foreground_threshold=self.alpha_matting_foreground_threshold,
            alpha_matting_background_threshold=self.alpha_matting_background_threshold,
            alpha_matting_erode_size=self.alpha_matting_erode_size,
        )


class AddColorGeneric(BaseModel):
    color: str = None
    color_name: str = None
    color_index: int = None
    palette: Optional[str]

    @validator("palette")
    def check_palette(cls, v):
        """Check palette value"""

        if v not in (valid_colors := list(COLORS)):
            raise ValueError(f"Color must be one from {valid_colors=}")
        return v

    @root_validator(pre=True)
    def populate_color(cls, values):
        """Infer color form color_name and color_index"""

        color_name = values.get("color_name")
        color_index = values.get("color_index")
        palette = values.get("palette")

        # Set a default if needed
        if palette is None:
            palette = "vtint"

        if (color_name is None) and (color_index is None):
            return values

        elif color_name is None:
            raise ValueError("'color_name' can't be null when 'color_index' is not null")

        elif color_index is None:
            raise ValueError("'color_index' can't be null when 'color_name' is not null")

        values["color"] = get_colors((color_name, color_index), palette=palette)
        return values

    @property
    def suffix(self):
        if self.action == "to_grayscale":
            prefix = "_grayscale"
        elif self.action == "round":
            prefix = "_round"
        else:
            prefix = ""

        if self.color_name and self.color_index:
            return f"{prefix}__{self.color_name}_{self.color_index}"

        elif self.color:
            return f"{prefix}__{self.color}"

        return prefix


class AddBackgroundColor(AddColorGeneric):
    action: Literal["add_background_color"]

    def run(self, image_in):
        return add_background_color(image_in, background_color=self.color)


class ToGrayscale(AddColorGeneric):
    action: Literal["to_grayscale"]

    def run(self, image_in):
        return to_grayscale(image_in, background_color=self.color)


class RoundImage(AddColorGeneric):
    action: Literal["round"]
    border_width: Optional[int]

    def run(self, image_in):
        return round_image(image_in, border_color=self.color, border_width=self.border_width)


class Job(BaseModel):
    transformations: list[Union[RoundImage, RemoveBg, AddBackgroundColor, ToGrayscale]]
    extension: str = None
    reprocess: bool = False

    @validator("extension", pre=True, always=True)
    def populate_extension(cls, v, values):
        transformations = values.get("transformations")
        last_transformation = transformations[-1]

        if isinstance(last_transformation, RoundImage) or isinstance(last_transformation, RemoveBg):
            return "png"
        return "jpg"

    @property
    def suffixes(self):
        out = ""
        for x in self.transformations:
            if x.action == "remove_bg":
                if len(self.transformations) == 1:
                    return x.suffix

            else:
                out += x.suffix

        return out

    def process(self, path_in, folder_out, name, save=True):
        folder_out = folder_out.rstrip("/")
        path_out = f"{folder_out}/{name}{self.suffixes}.{self.extension}"

        if not (self.reprocess or not os.path.exists(path_out)):
            return False

        image = get_image(path_in)

        for transformation in self.transformations:
            image = transformation.run(image)

        if self.extension in ("jpg", "jpeg"):
            image = image.convert("RGB")

        if not save:
            return image

        folder_out = path_out.rsplit("/", maxsplit=1)[0]
        if not os.path.exists(folder_out):
            os.makedirs(folder_out)

        image.save(path_out)
        return True


class Jobs(BaseModel):
    path_in: str
    folder_out: str
    jobs: list[Job]

    @property
    def name(self):
        return self.path_in.split("/")[-1].rsplit(".", maxsplit=1)[0]

    def do_all(self, tqdm_class=tqdm, tqdm_name=None):
        if tqdm_name is None:
            tqdm_name = self.name

        for job in tqdm_class(self.jobs, desc=tqdm_name):
            job.process(path_in=self.path_in, folder_out=self.folder_out, name=self.name)


def do_all(tqdm_class=tqdm):
    for filename in tqdm_class(os.listdir(PATH_JOBS), desc="do all"):
        if not filename.endswith(".yaml"):
            continue

        with open(f"{PATH_JOBS}/{filename}") as f:
            data = yaml.safe_load(f)

        jobs = Jobs(**data)
        jobs.do_all(tqdm_class=tqdm_class, tqdm_name=filename)


if __name__ == "__main__":
    do_all()
