from PIL import Image
from PIL import ImageDraw
from PIL import ImageOps
from rembg import remove
from vpalette import get_colors


def get_image(path_in):
    """Gets a pillow image"""
    return Image.open(path_in)


def remove_bg(image_in, alpha_matting=True, alpha_matting_erode_size=40, **kwargs):
    """Remove image background"""
    return remove(
        image_in,
        alpha_matting=alpha_matting,
        alpha_matting_erode_size=alpha_matting_erode_size,
        **kwargs
    )


def add_background_color(image_in, background_color, mask=None):
    """Fill background with solid color"""

    if mask is None:
        mask = image_in

    if type(background_color) is tuple:
        background_color = get_colors(background_color)

    image_out = Image.new("RGBA", image_in.size, background_color)
    image_out.paste(image_in, mask=mask)

    return image_out


def to_grayscale(image_in, background_color=None):
    """Turn image to grayscale"""

    return add_background_color(
        image_in.convert("L"), background_color=background_color, mask=image_in
    )


def round_image(image_in, border_color=None, border_width=None):
    """Rounds an image that must be squared"""
    mask = Image.new("L", image_in.size, 0)

    # Create circle mask
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + image_in.size, fill=255)

    # Apply mask
    image_out = ImageOps.fit(image_in, mask.size, centering=(0.5, 0.5))
    image_out.putalpha(mask)

    # Add border if needed
    if border_color and border_width:
        draw = ImageDraw.Draw(image_out)
        draw.arc((0, 0) + image_in.size, start=0, end=360, fill=border_color, width=border_width)

    return image_out
