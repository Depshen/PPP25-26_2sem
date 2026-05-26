import math as m
import itertools as itr
import functools as fn
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
def as_polygon(vertices):
    return tuple(tuple(v) for v in vertices)
def edge_vector(a, b):
    return b[0] - a[0], b[1] - a[1]
def determinant(v1, v2):
    return v1[0] * v2[1] - v1[1] * v2[0]
def combine(*actions):
    def execute(value):
        current = value
        for action in actions:
            current = action(current)
        return current
    return execute
def on_vertices(operation):
    def apply(poly):
        transformed = []
        for x, y in poly:
            transformed.append(operation((x, y)))
        return tuple(transformed)
    return apply
def gen_rectangle(width=1,
                  height=0.8,
                  gap=0.35,
                  start=-4,
                  level=0):
    step = width + gap
    position = start
    while True:
        x1 = position
        x2 = position + width
        y2 = level + height
        yield (
            (x1, level),
            (x2, level),
            (x2, y2),
            (x1, y2)
        )
        position += step
def gen_triangle(side=1,
                 gap=0.35,
                 start=-4,
                 level=0):
    h = side * m.sqrt(3) / 2
    shift = side + gap
    current = start
    while True:
        yield (
            (current, level),
            (current + side / 2, level + h),
            (current + side, level)
        )
        current += shift
def gen_triangle_flip(side=1,
                      gap=0.35,
                      start=-4,
                      level=0):
    h = side * m.sqrt(3) / 2
    shift = side + gap
    current = start
    while True:
        yield (
            (current + side, level),
            (current + side / 2, level - h),
            (current, level)
        )
        current += shift
def gen_hexagon(size=.55,
                gap=.35,
                start=-4,
                level=0):
    h = m.sqrt(3) * size
    move = size * 2 + gap
    x = start
    while True:
        poly = [
            (x + size/2, level),
            (x + 1.5*size, level),
            (x + 2*size, level+h/2),
            (x + 1.5*size, level+h),
            (x + size/2, level+h),
            (x, level+h/2)
        ]
        yield tuple(poly)
        x += move
def tr_translate(dx, dy):
    return on_vertices(
        lambda p:
        (p[0]+dx, p[1]+dy)
    )
def tr_rotate(angle, center=(0,0)):
    ox, oy = center
    c = m.cos(angle)
    s = m.sin(angle)
    def rotate(p):
        x = p[0]-ox
        y = p[1]-oy
        return (
            x*c-y*s+ox,
            x*s+y*c+oy
        )
    return on_vertices(rotate)
def tr_symmetry(mode):
    rules = {
        "x":
            lambda p: (p[0],-p[1]),
        "y":
            lambda p: (-p[0],p[1]),
        "origin":
            lambda p: (-p[0],-p[1])
    }
    return on_vertices(rules[mode])
def tr_homothety(k,
                 center=(0,0)):
    ox, oy = center
    def resize(p):
        return (
            ox+k*(p[0]-ox),
            oy+k*(p[1]-oy)
        )
    return on_vertices(resize)
def pipeline(stream, *operations):
    action = combine(*operations)
    for figure in stream:
        yield action(figure)
def show_polygons(data,
                  title="",
                  amount=None):
    fig, ax = plt.subplots(figsize=(9,5))
    if amount:
        data = itr.islice(data, amount)
    for poly in data:
        ax.add_patch(
            Polygon(
                poly,
                closed=True,
                fill=True,
                alpha=.15,
                edgecolor="black"
            )
        )
    ax.grid()
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_aspect("equal")
    ax.autoscale()
    plt.title(title)
    plt.show()
def sides(poly):
    temp = poly + (poly[0],)
    result=[]
    for a,b in zip(temp,temp[1:]):
        result.append(m.dist(a,b))
    return tuple(result)
def area(poly):
    closed = poly+(poly[0],)
    total=0
    for p1,p2 in zip(
            closed,
            closed[1:]
    ):
        total += (
            p1[0]*p2[1]
            -
            p2[0]*p1[1]
        )
    return abs(total)/2
def perimeter(poly):
    total=0
    for x in sides(poly):
        total += x
    return total
def distance_to_center(point):
    x,y=point
    return m.sqrt(
        x*x+y*y
    )


def agr_origin_nearest(current_closest_point, polygon):
    def get_closer_point(point1, point2):
        if distance_to_center(point1) < distance_to_center(point2):
            return point1
        return point2

    nearest_in_polygon = fn.reduce(get_closer_point, polygon)

    if current_closest_point is None:
        return nearest_in_polygon

    return get_closer_point(current_closest_point, nearest_in_polygon)


def agr_max_side(current_max_length, polygon):
    def get_larger_value(val1, val2):
        if val1 > val2:
            return val1
        return val2

    polygon_sides = sides(polygon)

    max_side_in_polygon = fn.reduce(get_larger_value, polygon_sides)

    if current_max_length is None:
        return max_side_in_polygon

    return get_larger_value(current_max_length, max_side_in_polygon)


def agr_min_area(current_min_area, polygon):
    polygon_area = area(polygon)

    if current_min_area is None:
        return polygon_area

    if polygon_area < current_min_area:
        return polygon_area
    return current_min_area


def agr_perimeter(total_perimeter, polygon):
    return total_perimeter + perimeter(polygon)


def agr_area(total_area, polygon):
    return total_area + area(polygon)


def flt_square(area_limit):
    def check_area(polygon):
        return area(polygon) < area_limit
    return check_area


def flt_short_side(length_limit):
    def check_shortest_side(polygon):
        shortest_side = min(sides(polygon))
        return shortest_side < length_limit
    return check_shortest_side


def create_stream_decorator(stream_processor):
    def decorator(generator_func):
        def wrapper(*args, **kwargs):
            original_stream = generator_func(*args, **kwargs)
            return stream_processor(original_stream)
        return wrapper
    return decorator


def tr_translate_decorator(dx, dy):
    def process_translation(stream):
        return map(tr_translate(dx, dy), stream)
    return create_stream_decorator(process_translation)


def tr_rotate_decorator(angle, center=(0, 0)):
    def process_rotation(stream):
        return map(tr_rotate(angle, center), stream)
    return create_stream_decorator(process_rotation)


def tr_symmetry_decorator(axis):
    def process_symmetry(stream):
        return map(tr_symmetry(axis), stream)
    return create_stream_decorator(process_symmetry)


def tr_homothety_decorator(k, center=(0, 0)):
    def process_homothety(stream):
        return map(tr_homothety(k, center), stream)
    return create_stream_decorator(process_homothety)


def flt_square_decorator(limit):
    def process_square_filter(stream):
        return filter(flt_square(limit), stream)
    return create_stream_decorator(process_square_filter)


def flt_short_side_decorator(limit):
    def process_short_side_filter(stream):
        return filter(flt_short_side(limit), stream)
    return create_stream_decorator(process_short_side_filter)


def zip_tuple(*items):
    result = ()
    for item in items:
        result += item
    return result


def count_2D(start_x=0, start_y=0, step_x=1, step_y=1):
    current_x = start_x
    current_y = start_y
    while True:
        yield (current_x, current_y)
        current_x += step_x
        current_y += step_y


def zip_polygons(*streams):
    for group in zip(*streams):
        merged_polygon = ()
        for polygon in group:
            merged_polygon += polygon
        yield merged_polygon

@tr_rotate_decorator(m.pi / 6)
def demo_rotation():
    return itr.islice(gen_rectangle(width=1, height=0.4, gap=0.2), 7)


@tr_symmetry_decorator("x")
def demo_symmetry():
    return itr.islice(gen_triangle(side=0.8, gap=0.2, level=0.5), 7)


@tr_homothety_decorator(0.7)
def demo_scale():
    return itr.islice(gen_hexagon(size=0.7), 7)


@flt_short_side_decorator(0.5)
def demo_filter():
    def apply_scale(k):
        transform = tr_homothety(k)
        return transform(((0, 0), (1, 0), (1, 0.4), (0, 0.4)))

    return map(apply_scale, itr.count(0.2, 0.15))


if __name__ == "__main__":
    show_polygons(gen_rectangle(), "Прямоугольники", 7)
    show_polygons(gen_triangle(), "Треугольники", 7)
    show_polygons(gen_hexagon(), "Шестиугольники", 7)

    rows = []
    for offset in (-0.6, 0, 0.6):
        rows.append(
            pipeline(
                itr.islice(gen_rectangle(width=1, height=0.35, gap=0.1), 7),
                tr_translate(0, offset),
                tr_rotate(m.pi / 6)
            )
        )
    show_polygons(itr.chain(*rows), "Три параллельные ленты")

    upper = itr.islice(gen_triangle(side=1, gap=0.2), 7)
    lower = itr.islice(gen_triangle_flip(side=1, gap=0.2), 7)
    show_polygons(zip_polygons(upper, lower), "Полигоны")

    sample = tuple(itr.islice(gen_rectangle(width=1, height=0.5, gap=0.2, start=-2), 5))

    print("Ближайший угол:", fn.reduce(agr_origin_nearest, sample, None))
    print("Максимальная сторона:", fn.reduce(agr_max_side, sample, None))
    print("Минимальная площадь:", fn.reduce(agr_min_area, sample, None))
    print("Суммарный периметр:", fn.reduce(agr_perimeter, sample, 0))
    print("Суммарная площадь:", fn.reduce(agr_area, sample, 0))

    print("\nzip_tuple:")
    print(zip_tuple((1, 2), (3, 4), (5, 6)))

    print("\ncount_2D:")
    points = tuple(itr.islice(count_2D(start_x=0, start_y=0, step_x=2, step_y=3), 5))
    print(points)

    print("\nzip_polygons:")
    p1 = iter([
        ((1, 1), (2, 2), (3, 1)),
        ((11, 11), (12, 12), (13, 11))
    ])
    p2 = iter([
        ((1, -1), (2, -2), (3, -1)),
        ((11, -11), (12, -12), (13, -11))
    ])
    print(list(zip_polygons(p1, p2)))

    print("\nДемонстрация декораторов")
    show_polygons(demo_rotation(), "Поворот через декоратор")
    show_polygons(demo_symmetry(), "Симметрия через декоратор")
    show_polygons(demo_scale(), "Гомотетия через декоратор")
    show_polygons(itr.islice(demo_filter(), 4), "Фильтрация через декоратор")

    print("\nРасширенное применение фильтров")

    def generate_transformed_figure(k):
        scale = tr_homothety(0.4 + k * 0.12)
        shift = tr_translate(k * 1.3 - 5, 0)
        base_polygon = ((0, 0), (1, 0), (1, 0.7), (0, 0.7))
        return shift(scale(base_polygon))

    figures = map(generate_transformed_figure, range(12))
    selected = tuple(itr.islice(filter(flt_square(1.2), figures), 6))

    print("Количество:", len(selected))
    show_polygons(selected, "Фильтр: ровно 6 фигур")

    def generate_scaled_figure(k):
        scale = tr_homothety(k)
        shift = tr_translate(k * 1.4, 0)
        base_polygon = ((0, 0), (1, 0), (1, 0.4), (0, 0.4))
        return shift(scale(base_polygon))

    scaled = map(generate_scaled_figure, itr.count(0.2, 0.15))
    result = tuple(itr.islice(filter(flt_short_side(0.25), itr.islice(scaled, 15)), 4))

    print("Короткая сторона:", len(result))
    show_polygons(result, "≤4 фигуры")

    def generate_overlapping_figure(x):
        shift = tr_translate(x * 0.3, 0)
        base_polygon = ((0, 0), (2, 0), (2, 1), (0, 1))
        return shift(base_polygon)

    overlapping = tuple(map(generate_overlapping_figure, range(15)))
    filtered = overlapping[::2]

    print("После удаления:", len(filtered))
    show_polygons(filtered, "Удалены пересекающиеся")
