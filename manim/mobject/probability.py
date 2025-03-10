"""Mobjects representing objects from probability theory and statistics."""

__all__ = ["SampleSpace", "BarChart"]


from typing import Iterable, Optional, Sequence, Union

import numpy as np
from colour import Color

from .. import config
from ..constants import *
from ..mobject.coordinate_systems import Axes
from ..mobject.geometry import Rectangle
from ..mobject.mobject import Mobject
from ..mobject.opengl_mobject import OpenGLMobject
from ..mobject.svg.brace import Brace
from ..mobject.svg.tex_mobject import MathTex, Tex
from ..mobject.types.vectorized_mobject import VGroup, VMobject
from ..utils.color import (
    BLUE_E,
    DARK_GREY,
    GREEN_E,
    LIGHT_GREY,
    MAROON_B,
    YELLOW,
    color_gradient,
)
from ..utils.iterables import tuplify

EPSILON = 0.0001


class SampleSpace(Rectangle):
    """

    Examples
    --------

    .. manim:: ExampleSampleSpace
        :save_last_frame:

        class ExampleSampleSpace(Scene):
            def construct(self):
                poly1 = SampleSpace(stroke_width=15, fill_opacity=1)
                poly2 = SampleSpace(width=5, height=3, stroke_width=5, fill_opacity=0.5)
                poly3 = SampleSpace(width=2, height=2, stroke_width=5, fill_opacity=0.1)
                poly3.divide_vertically(p_list=np.array([0.37, 0.13, 0.5]), colors=[BLACK, WHITE, GRAY], vect=RIGHT)
                poly_group = VGroup(poly1, poly2, poly3).arrange()
                self.add(poly_group)
    """

    def __init__(
        self,
        height=3,
        width=3,
        fill_color=DARK_GREY,
        fill_opacity=1,
        stroke_width=0.5,
        stroke_color=LIGHT_GREY,
        default_label_scale_val=1,
    ):
        super().__init__(
            height=height,
            width=width,
            fill_color=fill_color,
            fill_opacity=fill_opacity,
            stroke_width=stroke_width,
            stroke_color=stroke_color,
        )
        self.default_label_scale_val = default_label_scale_val

    def add_title(self, title="Sample space", buff=MED_SMALL_BUFF):
        # TODO, should this really exist in SampleSpaceScene
        title_mob = Tex(title)
        if title_mob.width > self.width:
            title_mob.width = self.width
        title_mob.next_to(self, UP, buff=buff)
        self.title = title_mob
        self.add(title_mob)

    def add_label(self, label):
        self.label = label

    def complete_p_list(self, p_list):
        new_p_list = list(tuplify(p_list))
        remainder = 1.0 - sum(new_p_list)
        if abs(remainder) > EPSILON:
            new_p_list.append(remainder)
        return new_p_list

    def get_division_along_dimension(self, p_list, dim, colors, vect):
        p_list = self.complete_p_list(p_list)
        colors = color_gradient(colors, len(p_list))

        last_point = self.get_edge_center(-vect)
        parts = VGroup()
        for factor, color in zip(p_list, colors):
            part = SampleSpace()
            part.set_fill(color, 1)
            part.replace(self, stretch=True)
            part.stretch(factor, dim)
            part.move_to(last_point, -vect)
            last_point = part.get_edge_center(vect)
            parts.add(part)
        return parts

    def get_horizontal_division(self, p_list, colors=[GREEN_E, BLUE_E], vect=DOWN):
        return self.get_division_along_dimension(p_list, 1, colors, vect)

    def get_vertical_division(self, p_list, colors=[MAROON_B, YELLOW], vect=RIGHT):
        return self.get_division_along_dimension(p_list, 0, colors, vect)

    def divide_horizontally(self, *args, **kwargs):
        self.horizontal_parts = self.get_horizontal_division(*args, **kwargs)
        self.add(self.horizontal_parts)

    def divide_vertically(self, *args, **kwargs):
        self.vertical_parts = self.get_vertical_division(*args, **kwargs)
        self.add(self.vertical_parts)

    def get_subdivision_braces_and_labels(
        self,
        parts,
        labels,
        direction,
        buff=SMALL_BUFF,
        min_num_quads=1,
    ):
        label_mobs = VGroup()
        braces = VGroup()
        for label, part in zip(labels, parts):
            brace = Brace(part, direction, min_num_quads=min_num_quads, buff=buff)
            if isinstance(label, (Mobject, OpenGLMobject)):
                label_mob = label
            else:
                label_mob = MathTex(label)
                label_mob.scale(self.default_label_scale_val)
            label_mob.next_to(brace, direction, buff)

            braces.add(brace)
            label_mobs.add(label_mob)
        parts.braces = braces
        parts.labels = label_mobs
        parts.label_kwargs = {
            "labels": label_mobs.copy(),
            "direction": direction,
            "buff": buff,
        }
        return VGroup(parts.braces, parts.labels)

    def get_side_braces_and_labels(self, labels, direction=LEFT, **kwargs):
        assert hasattr(self, "horizontal_parts")
        parts = self.horizontal_parts
        return self.get_subdivision_braces_and_labels(
            parts, labels, direction, **kwargs
        )

    def get_top_braces_and_labels(self, labels, **kwargs):
        assert hasattr(self, "vertical_parts")
        parts = self.vertical_parts
        return self.get_subdivision_braces_and_labels(parts, labels, UP, **kwargs)

    def get_bottom_braces_and_labels(self, labels, **kwargs):
        assert hasattr(self, "vertical_parts")
        parts = self.vertical_parts
        return self.get_subdivision_braces_and_labels(parts, labels, DOWN, **kwargs)

    def add_braces_and_labels(self):
        for attr in "horizontal_parts", "vertical_parts":
            if not hasattr(self, attr):
                continue
            parts = getattr(self, attr)
            for subattr in "braces", "labels":
                if hasattr(parts, subattr):
                    self.add(getattr(parts, subattr))

    def __getitem__(self, index):
        if hasattr(self, "horizontal_parts"):
            return self.horizontal_parts[index]
        elif hasattr(self, "vertical_parts"):
            return self.vertical_parts[index]
        return self.split()[index]


class BarChart(Axes):
    """Creates a bar chart. Inherits from :class:`~.Axes`, so it shares its methods
    and attributes. Each axis inherits from :class:`~.NumberLine`, so pass in ``x_axis_config``/``y_axis_config``
    to control their attributes.

    Parameters
    ----------
    values
        An iterable of values that determines the height of each bar. Accepts negative values.
    bar_names
        An iterable of names for each bar. Does not have to match the length of ``values``.
    y_range
        The y_axis range of values. If ``None``, the range will be calculated based on the
        min/max of ``values`` and the step will be calculated based on ``y_length``.
    x_length
        The length of the x-axis. If ``None``, it is automatically calculated based on
        the number of values and the width of the screen.
    y_length
        The length of the y-axis.
    bar_colors
        The color for the bars. Accepts a single color or an iterable of colors.
        If the length of``bar_colors`` does not match that of ``values``,
        intermediate colors will be automatically determined.
    bar_width
        The length of a bar. Must be between 0 and 1.
    bar_fill_opacity
        The fill opacity of the bars.
    bar_stroke_width
        The stroke width of the bars.

    Examples
    --------
    .. manim:: BarChartExample
        :save_last_frame:

        class BarChartExample(Scene):
            def construct(self):
                chart = BarChart(
                    values=[-5, 40, -10, 20, -3],
                    bar_names=["one", "two", "three", "four", "five"],
                    y_range=[-20, 50, 10],
                    y_length=6,
                    x_length=10,
                    x_axis_config={"font_size": 36},
                )

                c_bar_lbls = chart.get_bar_labels(font_size=48)

                self.add(chart, c_bar_lbls)
    """

    def __init__(
        self,
        values: Iterable[float],
        bar_names: Optional[Iterable[str]] = None,
        y_range: Optional[Sequence[float]] = None,
        x_length: Optional[float] = None,
        y_length: Optional[float] = config.frame_height - 4,
        bar_colors: Optional[Union[str, Iterable[str]]] = [
            "#003f5c",
            "#58508d",
            "#bc5090",
            "#ff6361",
            "#ffa600",
        ],
        bar_width: float = 0.6,
        bar_fill_opacity: float = 0.7,
        bar_stroke_width: float = 3,
        **kwargs,
    ):

        self.values = values
        self.bar_names = bar_names
        self.bar_colors = bar_colors
        self.bar_width = bar_width
        self.bar_fill_opacity = bar_fill_opacity
        self.bar_stroke_width = bar_stroke_width

        x_range = [0, len(self.values), 1]

        if y_range is None:
            y_range = [
                min(0, min(self.values)),
                max(0, max(self.values)),
                round(max(self.values) / y_length, 2),
            ]
        elif len(y_range) == 2:
            y_range = [*y_range, round(max(self.values) / y_length, 2)]

        if x_length is None:
            x_length = min(len(self.values), config.frame_width - 2)

        x_axis_config = {"font_size": 24, "label_constructor": Tex}
        self._update_default_configs(
            (x_axis_config,), (kwargs.pop("x_axis_config", None),)
        )

        self.bars = None
        self.x_labels = None
        self.bar_labels = None

        super().__init__(
            x_range=x_range,
            y_range=y_range,
            x_length=x_length,
            y_length=y_length,
            x_axis_config=x_axis_config,
            tips=kwargs.pop("tips", False),
            **kwargs,
        )

        self._add_bars()

        if self.bar_names is not None:
            self._add_x_axis_labels()

        self.y_axis.add_numbers()

    def _add_x_axis_labels(self):
        """Essentially ``:meth:~.NumberLine.add_labels``, but differs in that
        the direction of the label with respect to the x_axis changes to UP or DOWN
        depending on the value.

        UP for negative values and DOWN for positive values.
        """

        val_range = np.arange(
            0.5, len(self.bar_names), 1
        )  # 0.5 shifted so that labels are centered, not on ticks

        labels = VGroup()

        for i, (value, bar_name) in enumerate(zip(val_range, self.bar_names)):
            # to accommodate negative bars, the label may need to be
            # below or above the x_axis depending on the value of the bar
            if self.values[i] < 0:
                direction = UP
            else:
                direction = DOWN
            bar_name_label = self.x_axis.label_constructor(bar_name)

            bar_name_label.font_size = self.x_axis.font_size
            bar_name_label.next_to(
                self.x_axis.number_to_point(value),
                direction=direction,
                buff=self.x_axis.line_to_number_buff,
            )

            labels.add(bar_name_label)

        self.x_axis.labels = labels
        self.x_axis.add(labels)

    def _add_bars(self):
        self.bars = VGroup()

        for i, value in enumerate(self.values):
            bar_h = abs(self.c2p(0, value)[1] - self.c2p(0, 0)[1])
            bar_w = self.c2p(self.bar_width, 0)[0] - self.c2p(0, 0)[0]
            bar = Rectangle(
                height=bar_h,
                width=bar_w,
                stroke_width=self.bar_stroke_width,
                fill_opacity=self.bar_fill_opacity,
            )

            pos = UP if (value >= 0) else DOWN
            bar.next_to(self.c2p(i + 0.5, 0), pos, buff=0)
            self.bars.add(bar)
        if isinstance(self.bar_colors, str):
            self.bars.set_color_by_gradient(self.bar_colors)
        else:
            self.bars.set_color_by_gradient(*self.bar_colors)

        self.add_to_back(self.bars)

    def get_bar_labels(
        self,
        color: Optional[Color] = None,
        font_size: float = 24,
        buff: float = MED_SMALL_BUFF,
        label_constructor: "VMobject" = Tex,
    ):
        """Annotates each bar with its corresponding value. Use ``self.bar_labels`` to access the
        labels after creation.

        Parameters
        ----------
        color
            The color of each label. By default ``None`` and is based on the parent's bar color.
        font_size
            The font size of each label.
        buff
            The distance from each label to its bar. By default 0.4.
        label_constructor
            The Mobject class to construct the labels, by default :class:`~.Tex`.

        Examples
        --------
        .. manim:: GetBarLabelsExample
            :save_last_frame:

            class GetBarLabelsExample(Scene):
                def construct(self):
                    chart = BarChart(values=[10, 9, 8, 7, 6, 5, 4, 3, 2, 1], y_range=[0, 10, 1])

                    c_bar_lbls = chart.get_bar_labels(
                        color=WHITE, label_constructor=MathTex, font_size=36
                    )

                    self.add(chart, c_bar_lbls)

        """

        bar_labels = VGroup()
        for bar, value in zip(self.bars, self.values):
            bar_lbl = label_constructor(str(value))

            if color is None:
                bar_lbl.set_color(bar.get_fill_color())
            else:
                bar_lbl.set_color(color)

            bar_lbl.font_size = font_size

            pos = UP if (value >= 0) else DOWN
            bar_lbl.next_to(bar, pos, buff=buff)
            bar_labels.add(bar_lbl)

        return bar_labels

    def change_bar_values(self, values: Iterable[float]):
        """Updates the height of the bars of the chart.

        Parameters
        ----------
        values
            The values that will be used to update the height of the bars.
            Does not have to match the number of bars.

        Examples
        --------

        .. manim:: ChangeBarValuesExample
            :save_last_frame:

            class ChangeBarValuesExample(Scene):
                def construct(self):
                    values=[-10, -8, -6, -4, -2, 0, 2, 4, 6, 8, 10]

                    chart = BarChart(
                        values,
                        y_range=[-10, 10, 2],
                        y_axis_config={"font_size": 24},
                    )
                    self.add(chart)

                    chart.change_bar_values(list(reversed(values)))
                    self.add(chart.get_bar_labels(font_size=24))
        """

        for i, (bar, value) in enumerate(zip(self.bars, values)):
            chart_val = self.values[i]

            if chart_val > 0:
                bar_lim = bar.get_bottom()
                aligned_edge = DOWN
            else:
                bar_lim = bar.get_top()
                aligned_edge = UP

            try:
                quotient = value / chart_val
                if quotient < 0:

                    aligned_edge = UP if chart_val > 0 else DOWN

                    # if the bar is already positive, then we now want to move it
                    # so that it is negative. So, we move the top edge of the bar
                    # to the location of the previous bottom

                    # if already negative, then we move the bottom edge of the bar
                    # to the location of the previous top

                bar.stretch_to_fit_height(quotient * bar.height)

            except ZeroDivisionError:
                bar.height = 0

            bar.move_to(bar_lim, aligned_edge)

        self.values[: len(values)] = values
