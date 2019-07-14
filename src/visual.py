import tempfile
import tkinter as tk

from matplotlib.figure import Figure as mplFigure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import PIL
from PIL.ImageTk import PhotoImage as tkPhotoImage
import PIL.ImageEnhance


# This is a bit tricky / ugly.
# matplotlib does not allow us to specify exact pixel values.
# So we need to use a hack here.
def createFigureCanvas(width, height, axes=None):
    if axes is None:
        axes = [0., 0., 1., 1.]

    fig = mplFigure(frameon=False)
    DPI = float(fig.get_dpi())

    fCanvas = FigureCanvas(fig)
    fig.set_size_inches(width/DPI, height/DPI)

    # We don't want any axes drawn, of course.
    ax = fig.add_axes(axes)
    ax.set_axis_off()
    return (ax, fCanvas, DPI)


# This seems to be the only way to get an exact pixel count:
# Save the image to a file and specify dpi to use.
def canvasImage(fCanvas, dpi):
    f = tempfile.TemporaryFile()
    fCanvas.print_figure(f, dpi=dpi)
    return PIL.Image.open(f)


def createHeatmap(width, height, values):
    (ax, fCanvas, dpi) = createFigureCanvas(width, height)

    # cmap sets the used (predefined) colormap
    ax.matshow(values, cmap='inferno', interpolation='bicubic')
    img = canvasImage(fCanvas, dpi)
    # Flip image, because canvas y-coordinates increase downwards...
    img = img.transpose(PIL.Image.FLIP_TOP_BOTTOM)
    return tkPhotoImage(img)


def createVectorPlot(width, height, gridX, gridY, vectors, col):
    zx = width*1.1
    zy = height*1.1
    dx = zx - width
    dy = zy - height

    (ax, fCanvas, dpi) = createFigureCanvas(width=zx, height=zy)
    ax.quiver(gridX,
              gridY,
              vectors[:,:,0],
              vectors[:,:,1],
              angles='xy',
              facecolor=col,
              antialiased=True)

    img = canvasImage(fCanvas, dpi)
    img = img.crop((dx/2, dy/2, zx - dx/2, zy - dy/2))
    meh = PIL.ImageEnhance.Sharpness(img)
    # Smooth out ugly pixelated arrows
    img = meh.enhance(0.4)
    # for some reason, this is exceedingly slow in this case:
    # self._vectorImage = tkPhotoImage(img)
    # It has to do with image transparency, which is not really
    # supported by Tkinter. But I'm not sure about the details.
    img = img.convert(mode='RGB')
    return tkPhotoImage(img)