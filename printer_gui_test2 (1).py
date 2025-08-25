import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout,
    QFileDialog, QTextEdit, QGraphicsView, QGraphicsScene, QGraphicsLineItem,
    QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsSimpleTextItem
)
from PyQt5.QtGui import QPen, QFont
from PyQt5.QtCore import Qt
import linuxcnc
import os

class LinuxCNCGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.status = linuxcnc.stat()
        self.command = linuxcnc.command()
        self.drawing = None
        self.start_point = None
        self.polyline_points = []
        self.coord_label_item = QGraphicsSimpleTextItem()
        self.coord_label_item.setFont(QFont("Courier", 10))
        self.coord_label_item.setZValue(1000)
        self.scene.addItem(self.coord_label_item)

    def initUI(self):
        layout = QVBoxLayout()
        self.status_label = QLabel("LinuxCNC Status: Unknown")
        layout.addWidget(self.status_label)

        control_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start")
        self.start_btn.clicked.connect(self.start_machine)
        control_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_machine)
        control_layout.addWidget(self.stop_btn)
        layout.addLayout(control_layout)

        jog_layout = QHBoxLayout()
        self.jog_x_neg = QPushButton("X-")
        self.jog_x_neg.clicked.connect(lambda: self.jog_axis('x', -1))
        jog_layout.addWidget(self.jog_x_neg)

        self.jog_x_pos = QPushButton("X+")
        self.jog_x_pos.clicked.connect(lambda: self.jog_axis('x', 1))
        jog_layout.addWidget(self.jog_x_pos)
        layout.addLayout(jog_layout)

        file_layout = QHBoxLayout()
        self.load_gcode_btn = QPushButton("Load G-Code")
        self.load_gcode_btn.clicked.connect(self.load_gcode)
        file_layout.addWidget(self.load_gcode_btn)

        self.save_gcode_btn = QPushButton("Save G-Code")
        self.save_gcode_btn.clicked.connect(self.save_gcode)
        file_layout.addWidget(self.save_gcode_btn)
        layout.addLayout(file_layout)

        draw_layout = QHBoxLayout()
        for label, action in [
            ("Line", "line"),
            ("Rectangle", "rectangle"),
            ("Circle", "circle"),
            ("Ellipse", "ellipse"),
            ("Polyline", "polyline"),
            ("Clear Canvas", "clear")
        ]:
            btn = QPushButton(label)
            if action == "clear":
                btn.clicked.connect(self.clear_canvas)
            else:
                btn.clicked.connect(lambda checked, a=action: self.start_drawing(a))
            draw_layout.addWidget(btn)
        layout.addLayout(draw_layout)

        self.gen_gcode_btn = QPushButton("Generate G-code")
        self.gen_gcode_btn.clicked.connect(self.generate_gcode)
        layout.addWidget(self.gen_gcode_btn)

        #  Send to LinuxCNC button
        self.send_gcode_btn = QPushButton("Send to LinuxCNC")
        self.send_gcode_btn.setEnabled(False)  # Disable initially
        self.send_gcode_btn.clicked.connect(self.send_gcode_to_linuxcnc)
        layout.addWidget(self.send_gcode_btn)
        
        display_layout = QHBoxLayout()

        self.gcode_display = QTextEdit()
        self.gcode_display.setReadOnly(True)
        self.gcode_display.setFixedWidth(250)
        display_layout.addWidget(self.gcode_display)

        self.graphics_view = QGraphicsView()
        self.scene = QGraphicsScene()
        self.graphics_view.setScene(self.scene)
        self.graphics_view.setMouseTracking(True)
        self.graphics_view.viewport().installEventFilter(self)
        display_layout.addWidget(self.graphics_view)

        layout.addLayout(display_layout)

        self.setLayout(layout)
        self.setWindowTitle("LinuxCNC GUI")
        self.resize(800, 600)

    def start_machine(self):
        self.command.state(linuxcnc.STATE_ON)
        self.update_status()

    def stop_machine(self):
        self.command.state(linuxcnc.STATE_OFF)
        self.update_status()

    def jog_axis(self, axis, direction):
        jog_cmd = {"x": 0, "y": 1, "z": 2}
        if axis in jog_cmd:
            self.command.jog(linuxcnc.JOG_CONTINUOUS, jog_cmd[axis], direction * 5, 0)

    def update_status(self):
        self.status.poll()
        state_map = {
            linuxcnc.STATE_ESTOP: "ESTOP",
            linuxcnc.STATE_ESTOP_RESET: "ESTOP RESET",
            linuxcnc.STATE_ON: "ON",
            linuxcnc.STATE_OFF: "OFF",
        }
        self.status_label.setText(f"LinuxCNC Status: {state_map.get(self.status.state, 'UNKNOWN')}")

    def load_gcode(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open G-Code File", "", "G-Code Files (*.ngc *.nc *.gcode)")
        if file_name:
            with open(file_name, 'r') as file:
                self.gcode_display.setText(file.read())

    def save_gcode(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Save G-Code", "", "G-Code Files (*.ngc)")
        if file_name:
            with open(file_name, 'w') as f:
                f.write(self.gcode_display.toPlainText())

    def start_drawing(self, shape):
        self.drawing = shape
        self.start_point = None
        self.polyline_points = []

    def clear_canvas(self):
        for item in self.scene.items():
            if item != self.coord_label_item:
                self.scene.removeItem(item)

    def eventFilter(self, source, event):
        if event.type() == 2:  # Mouse press
            pos = self.graphics_view.mapToScene(event.pos())
            if self.drawing == "polyline":
                self.polyline_points.append(pos)
                if len(self.polyline_points) > 1:
                    pen = QPen(Qt.black)
                    p1 = self.polyline_points[-2]
                    p2 = self.polyline_points[-1]
                    line = self.scene.addLine(p1.x(), p1.y(), p2.x(), p2.y(), pen)
                    line.setData(0, "line")
                    self.make_editable(line)
            else:
                self.start_point = pos

        elif event.type() == 3 and self.start_point and self.drawing != "polyline":
            end_point = self.graphics_view.mapToScene(event.pos())
            pen = QPen(Qt.black)
            shape_item = None
            text = ""

            if self.drawing == "line":
                shape_item = QGraphicsLineItem(self.start_point.x(), self.start_point.y(), end_point.x(), end_point.y())
                text = f"{((end_point - self.start_point).manhattanLength()):.2f} mm"

            elif self.drawing == "rectangle":
                width = end_point.x() - self.start_point.x()
                height = end_point.y() - self.start_point.y()
                shape_item = QGraphicsRectItem(self.start_point.x(), self.start_point.y(), width, height)
                text = f"{abs(width):.2f}x{abs(height):.2f} mm"

            elif self.drawing == "circle":
                r = min(abs(end_point.x() - self.start_point.x()), abs(end_point.y() - self.start_point.y()))
                shape_item = QGraphicsEllipseItem(self.start_point.x(), self.start_point.y(), r, r)
                text = f"R={r/2:.2f} mm"

            elif self.drawing == "ellipse":
                width = end_point.x() - self.start_point.x()
                height = end_point.y() - self.start_point.y()
                shape_item = QGraphicsEllipseItem(self.start_point.x(), self.start_point.y(), width, height)
                text = f"{abs(width):.2f}x{abs(height):.2f} mm"

            if shape_item:
                shape_item.setPen(pen)
                shape_item.setData(0, self.drawing)
                self.make_editable(shape_item)
                self.scene.addItem(shape_item)

                dim_text = QGraphicsSimpleTextItem(text)
                dim_text.setFont(QFont("Arial", 8))
                dim_text.setPos(end_point.x() + 10, end_point.y() + 10)
                dim_text.setZValue(999)
                self.scene.addItem(dim_text)

            self.start_point = None

        elif event.type() == 5:  # Mouse move
            pos = self.graphics_view.mapToScene(event.pos())
            self.coord_label_item.setText(f"X: {pos.x():.2f}, Y: {pos.y():.2f}")
            self.coord_label_item.setPos(pos.x() + 10, pos.y() + 10)

        return super().eventFilter(source, event)

    def make_editable(self, item):
        item.setFlag(item.ItemIsMovable, True)
        item.setFlag(item.ItemIsSelectable, True)

    def generate_gcode(self):
        shapes = [item for item in self.scene.items() if item.data(0) in ["line", "rectangle", "circle", "ellipse", "polyline"] and hasattr(item, 'boundingRect')]


        if not shapes:
            self.gcode_display.setText("No valid shapes to generate G-code.")
            return

    # Step 1: Find bounding box of all shapes
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')

        for item in shapes:
            rect = item.boundingRect()
            min_x = min(min_x, rect.left())
            min_y = min(min_y, rect.top())
            max_x = max(max_x, rect.right())
            max_y = max(max_y, rect.bottom())

        drawing_width = max_x - min_x
        drawing_height = max_y - min_y

    # Step 2: Machine limits
        machine_x_range = 20.0  # From -10 to 10
        machine_y_range = 20.0  # From -10 to 10
        margin = 1.0            # Leave 1mm margin

        scale_x = (machine_x_range - 2 * margin) / drawing_width
        scale_y = (machine_y_range - 2 * margin) / drawing_height
        scale = min(scale_x, scale_y)

    # Step 3: Translate and scale so it fits
        def transform(x, y):
            tx = (x - min_x) * scale - (drawing_width * scale / 2)  # Centered at X=0
            ty = (y - min_y) * scale - (drawing_height * scale / 2)  # Centered at Y=0
            return tx, ty
            
        SAFE_Z = 0.1
        CUT_Z = -1.0

        gcode_lines = [
            "G21",    # mm
            "G90",    # absolute
            f"G0 Z{SAFE_Z:.2f}"   # Safe lift
        ]

        for item in shapes:
             shape = item.data(0)
             
             if shape == "line" and isinstance(item, QGraphicsLineItem):
                line = item.line()
                x1, y1 = transform(line.x1(), line.y1())
                x2, y2 = transform(line.x2(), line.y2())
                gcode_lines.append(f"G0 X{x1:.2f} Y{y1:.2f}")
                gcode_lines.append("G1 Z-1.00 F100")
                gcode_lines.append(f"G1 X{x2:.2f} Y{y2:.2f} F300")
                gcode_lines.append(f"G0 Z{SAFE_Z:.2f}")

             elif shape == "rectangle" and isinstance(item, QGraphicsRectItem):
                r = item.rect()
                p1 = transform(r.left(), r.top())
                p2 = transform(r.right(), r.top())
                p3 = transform(r.right(), r.bottom())
                p4 = transform(r.left(), r.bottom())
                gcode_lines.append(f"G0 X{p1[0]:.2f} Y{p1[1]:.2f}")
                gcode_lines.append("G1 Z-1.00 F100")
                gcode_lines.append(f"G1 X{p2[0]:.2f} Y{p2[1]:.2f}")
                gcode_lines.append(f"G1 X{p3[0]:.2f} Y{p3[1]:.2f}")
                gcode_lines.append(f"G1 X{p4[0]:.2f} Y{p4[1]:.2f}")
                gcode_lines.append(f"G1 X{p1[0]:.2f} Y{p1[1]:.2f}")
                gcode_lines.append(f"G0 Z{SAFE_Z:.2f}")

             elif shape == "circle" and isinstance(item, QGraphicsEllipseItem):
                 r = item.rect()
                 if r.width() == r.height():
                     radius = r.width() / 2

                     # Transform center
                     center_x_raw = r.x() + radius
                     center_y_raw = r.y() + radius
                     center_x, center_y = transform(center_x_raw, center_y_raw)

                     # Transformed start point (top of circle)
                     start_x, start_y = center_x, center_y + (radius * scale)


                     gcode_lines.append(f"G0 X{start_x:.2f} Y{start_y:.2f}")
                     gcode_lines.append(f"G1 Z{CUT_Z:.2f} F100")

                     # First half (top to bottom)
                     gcode_lines.append(f"G3 X{start_x:.2f} Y{center_y - radius * scale:.2f} I0.00 J{-radius * scale:.2f}")
                     # Second half (bottom to top)
                     gcode_lines.append(f"G3 X{start_x:.2f} Y{start_y:.2f} I0.00 J{radius * scale:.2f}")
   
                     gcode_lines.append(f"G0 Z{SAFE_Z:.2f}")  

        gcode_lines.append("M30")
        self.gcode_display.setText("\n".join(gcode_lines))
        self.send_gcode_btn.setEnabled(True)


    def send_gcode_to_linuxcnc(self):
        gcode = self.gcode_display.toPlainText()
        if not gcode.strip():
            print("No G-code to send.")
            return

        try:
            path = "/tmp/gui_output.ngc"
            with open(path, "w") as f:
                f.write(gcode)

            self.command.state(linuxcnc.STATE_ESTOP_RESET)
            self.command.wait_complete()

            self.command.state(linuxcnc.STATE_ON)
            self.command.wait_complete()

            self.command.mode(linuxcnc.MODE_AUTO)
            self.command.wait_complete()

            self.command.program_open(path)
            self.command.wait_complete()

            #  Start execution from beginning
            self.command.start(0)
            self.command.wait_complete()

            print("G-code file sent to LinuxCNC and execution started.")

        except Exception as e:
            print(f"Error sending G-code: {e}")




if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LinuxCNCGUI()
    window.show()
    sys.exit(app.exec_())
