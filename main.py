#!/usr/bin/env python3

from tkinter import Tk, Canvas, Frame, BOTH, EventType
from math import sin, cos, pi, atan
from random import randint, choice

from shapes import ShapeCombination, Cube, SquarePyramid
from matrix import Matrix as M, Vector as V


CURSOR_VIS = {False: 'none', True: ''}

def z_rotator(angle):  # right hand rule rotation!
    return M(  # y unchanged, x and z move along a circle
        [cos(angle), -sin(angle), 0],
        [sin(angle), cos(angle), 0],
        [0, 0, 1],
    )
def x_rotator(angle):
    return M(  # x unchanged, y and z move along a circle
        [1, 0, 0],
        [0, cos(angle), -sin(angle)],
        [0, sin(angle), cos(angle)],
    )
obj_rotator = z_rotator(pi/32)  # very small angle

# LA skript: matrix multiplication is associative!

def draw_circle(v, r, canvas, color='black'):
    x,y = v.value
    if r < 0:
        r = 0

    x0 = x - r
    y0 = y - r
    x1 = x + r
    y1 = y + r
    return canvas.create_oval(x0, y0, x1, y1, fill=color, tag='clearable')

def projection(v, camera, centre):
    v -= camera.pos  # camera is basically the origin after this
    v = x_rotator(camera.x_rotation_angle) * v  # rotate points on x-axis around camera
    v = z_rotator(camera.z_rotation_angle) * v  # rotate points on z-axis around camera
    
    sx = 1/v.length  # more distance => point closer to middle (?)
    sy = 1/v.length
    sx *= 800  # zoom way in (original pyramid is tiny)
    sy *= -800  # tk has y pointing down
    res = M((sx,0,0), (0,0,sy)) * v  # Apply transform from Q3 to Q2
    res += centre  # move to the middle
    return res

class Camera:
    def __init__(self, pos=V(0,-10,0), view=V(0,1,0), speed=0.1, rot_speed=pi/64):
        self.pos = pos
        self.view = view
        self.speed = speed
        self.rot_speed = rot_speed
    
    @property
    def x(self):
        return self.view.value[0]
    
    @property
    def y(self):
        return self.view.value[1]
    
    @property
    def z(self):
        return self.view.value[2]
    
    @property
    def z_rotation_angle(self):
        if not self.y:
            return pi  # think of better solution
        return atan(self.x/self.y)
    
    @property
    def x_rotation_angle(self):
        if not self.y:
            return pi
        return atan(self.z/self.y)

    def move(self, v):
        self.pos += v*self.speed
    
    def turn(self, rad_x, rad_z):
        rot_matrix = x_rotator(rad_x) * z_rotator(rad_z)  # two M*v would be (3x) faster, but this is waay cooler
        self.view = rot_matrix * self.view


class Window:
    KEY_BINDINGS = {
        'w': V(0,1,0),
        'a': V(-1,0,0),
        's': V(0,-1,0),
        'd': V(1,0,0),
        ' ': V(0,0,1),
        'q': V(0,0,-1),
        'i': V(1,0),
        'j': V(0,1),
        'k': V(-1,0),
        'l': V(0,-1),
    }

    def __init__(self, root, canvas, shape):  #, width, height):
        self.root = root
        self.canvas = canvas
        self.shape = shape
        self.width = 1366
        self.height = 744

        self.w2 = self.width/2
        self.h2 = self.height/2
        self.mouse = [0, 0]
        self.paused = False
        self.paused_text = canvas.create_text(self.w2, 10, anchor="n", font='Arial 50')

        self.root.attributes('-zoomed', True)
        self.root.config(cursor='none')
        self.canvas.pack(fill=BOTH, expand=1)
        
        self.centre = V(self.w2, self.h2)
        self.refresh = 50
        self.camera = Camera()

        self.canvas.bind_all('<w>', self.move_input)
        self.canvas.bind_all('<a>', self.move_input)
        self.canvas.bind_all('<s>', self.move_input)
        self.canvas.bind_all('<d>', self.move_input)
        self.canvas.bind_all('<q>', self.move_input)
        self.canvas.bind_all('<space>', self.move_input)
        
        self.canvas.bind_all('<j>', self.turn_input)
        self.canvas.bind_all('<l>', self.turn_input)
        self.canvas.bind_all('<i>', self.turn_input)
        self.canvas.bind_all('<k>', self.turn_input)
        self.canvas.bind('<Motion>', self.turn_input)
        
        self.canvas.bind_all('<p>', self.toggle_motion)
        self.canvas.bind_all('<Escape>', self.toggle_motion)
        self.canvas.bind_all('<Leave>', self.pause_motion)
        self.canvas.bind_all('<Control-r>', self.reset_camera)
        self.canvas.bind_all('<Control-c>', self.quit)
    
    def start(self):
        self.draw()
        self.root.mainloop()

    def draw(self):
        self.canvas.delete('clearable')

        self.camera.turn(*self.mouse_to_angles())
        root.event_generate('<Motion>', warp=True, x=self.w2, y=self.h2)  # stick mouse in the middle
        self.mouse = [0, 0]
        
        converted_points = []
        
        for v in self.shape.points:
            converted = projection(v, self.camera, self.centre)
            converted_points.append(converted)
            #draw_circle(converted, 3-v.value[2], canvas, 'red')

        for f in self.shape.faces:
            p = self.canvas.create_polygon(*(converted_points[x].value for x in f), tag='clearable')
            # self.canvas.itemconfigure(p, fill='#'+''.join([choice('012356789abcdef') for x in range(6)]))
            self.canvas.itemconfigure(p, fill='#660033')  # stipple='gray50'
            
        for p1, p2 in self.shape.lines:
            p1_vect = converted_points[p1]
            p2_vect = converted_points[p2]
            self.canvas.create_line(*p1_vect.value, *p2_vect.value, tag='clearable')

        self.shape.transform(obj_rotator)  # yo linear algebra works

        if not self.paused:
            self.root.after(self.refresh, self.draw)
    
    def turn_input(self, event):
        if self.paused:
            return
        if event.type == EventType.Motion:  # handle mouse movement
            if (event.x, event.y) != self.centre.value:
                self.mouse[0] += event.x - self.centre.value[0]
                self.mouse[1] += event.y - self.centre.value[1]
        elif event.type == EventType.Key:  # handle key presses
            v = self.KEY_BINDINGS.get(event.char, (0,0))
            v *= pi/64  # TODO make sensitivity?
            self.camera.turn(*v.value)
    
    def move_input(self, event):
        if self.paused:
            return
        v = self.KEY_BINDINGS.get(event.char, V(0,0,0))
        self.camera.move(v)
    
    def mouse_to_angles(self):  # x-rotation depends on y-position of mouse, and vice versa
        mx, my = self.mouse
        self.mouse = [0,0]
        x = my*pi/1000  # TODO make denominator the sensitivity?
        y = -mx*pi/1000  # TODO invert y-axis with the negative sign?
        return x, y
    
    def pause_motion(self, event):
        if not self.paused:
            self.toggle_motion()  # keep the pause code in one place
    
    def toggle_motion(self, event):
        self.paused = not self.paused
        self.root.config(cursor=CURSOR_VIS[self.paused])
        self.canvas.itemconfig(self.paused_text, text='PAUSED')
        if not self.paused:
            self.draw()
            self.canvas.itemconfig(self.paused_text, text='')

    def quit(self, *args):
        self.root.destroy()

    def reset_camera(self, event):
        self.camera = Camera()  # TODO add a way of resetting to non-standard camera?

myShape = ShapeCombination(
    Cube(V(0,0,0)),
    Cube(V(0,0,1)),
    SquarePyramid(V(0,0,2)),
    Cube(V(2,0,0)),
    Cube(V(2,0,1)),
    SquarePyramid(V(2,0,2)),
    Cube(V(1,0,1)),
    shift=V(-1.5,-0.5,-1.5),
)

if __name__ == '__main__':
    root = Tk()
    canvas = Canvas(root)
    
    window = Window(root, canvas, myShape)
    window.start()

