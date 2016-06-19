import struct
import struct_helper


class PyxpressoModel(object):
    def __init__(self):
        self.frames = []

    def add_frame(self, frame):
        # types; (PyxpressoFrame) -> None
        assert isinstance(frame, PyxpressoFrame)
        self.frames.append(frame)

    def export_unreal_data(self, filename):
        if len(self.frames) < 1:
            return False

        open(filename, "w").truncate()

        unreal_data_file = struct_helper.BinaryFile(filename)

        unreal_data_file.write_binary(
            False,
            "4H5L1B",
            len(self.frames[0].polygons),
            len(self.frames[1].vertices),
            *((0,) * 8)
        )

        for polygon in self.frames[0].polygons:
            unreal_data_file.write_binary(
                False,
                "3H2b6B2b",
                polygon[0][0],
                polygon[0][1],
                polygon[0][2],
                1,
                polygon[1][0][0],
                polygon[1][0][1],
                polygon[1][1][0],
                polygon[1][1][1],
                polygon[1][2][0],
                polygon[1][2][1],
                1,
                0
            )

        return True

    def export_unreal_aniv(self, filename):
        if len(self.frames) < 1:
            return False

        unreal_aniv_file = struct_helper.BinaryFile(filename)

        unreal_aniv_file.write_binary(
            False,
            "2h",
            len(self.frames),
            len(self.frames[0].vertices) * struct.calcsize("L")
        )

        for frame in self.frames:
            for vertex in frame.vertices:
                vertex_long = int(vertex[0] * 8.0) & 0x7ff | \
                            ((int(vertex[1] * 8.0) & 0x7ff) << 11) | \
                            ((int(vertex[2] * 4.0) & 0x3ff) << 22)

                unreal_aniv_file.write_binary(
                    False,
                    "L",
                    vertex_long
                )

        return True


class PyxpressoFrame(object):
    def __init__(self, vertices=(), polygons=(), uv_coord=()):
        self.vertices = list(vertices)
        self.polygons = list(polygons)
        self.uv_coord = list(uv_coord)

    def check_command(self, data, functions):
        # types: (str, dict(str: function)) -> None
        for kind, func in functions.items():
            if data.startswith(kind + " "):
                functions(data.split(" ")[1:])

    def parse_obj_vertex(self, data):
        self.vertices.append(tuple([int(coordinate) for coordinate in data][:3]))

    def parse_obj_polygon(self, data):
        vertex_data = [item.split("/") for item in data]

        for vertex_index in [int(index[0]) for index in vertex_data]:
            if vertex_index > len(self.vertices):
                print "Warning: One of the polygons parsed references a unexistant vertex index! " \
                      "(index {} of polygon {})".format(vertex_index, len(self.polygons))

        for uv_coord_index in [int(index[1]) for index in vertex_data]:
            if uv_coord_index > len(self.uv_coord):
                print "Warning: One of polygons parsed references a unexistant UV coordinate index! " \
                      "(index {} of polygon {})".format(uv_coord_index, len(self.polygons))

        self.polygons.append((
            tuple([int(index[0]) for index in vertex_data]),
            tuple([int(index[1]) for index in vertex_data])
        ))

    def parse_obj_uv_coordinates(self, data):
        self.uv_coord.append(tuple([int(coordinate) for coordinate in data][:2]))

    def clear_model_data(self):
        model = PyxpressoFrame(self.vertices, self.polygons, self.uv_coord)

        self.vertices = self.uv_coord = self.polygons = []

        return model

    def parse_obj_frame(self, obj_filename):
        obj_data = open(obj_filename).readlines()

        for item in obj_data:
            self.check_command(item, {"v": self.parse_obj_vertex, "f": self.parse_obj_polygon,
                                      "vt": self.parse_obj_uv_coordinates})
