from matrix import Matrix, Vector

conv = lambda v : Vector(*v)
v0 = Vector(0,0,0)
m1 = Matrix((1,0,0),(0,1,0),(0,0,1))

class Shape():
    DEFAULT_POINTS = [v0]  # first points is the 'anchor'
    LINES = []

    def __init__(self, shift=v0, trans=m1):
        self.reset()
        self.move_to(shift)
        self.transform(trans)
    
    @property
    def cur(self):
        return self.points[0]
    
    def reset(self):
        self.points = self.DEFAULT_POINTS[:]
        self.lines = self.LINES[:]
    
    def move_to(self, pos):
        self.points = [v-self.cur+pos for v in self.points]
    
    def move_by(self, pos):
        self.points = [v+pos for v in self.points]
    
    def transform(self, m):  # apply matrix transform to all points
        self.points = [m*v for v in self.points]
        if m.det == 0:  # optimisation only needed if det=0 ( <=> 1 or more dimentions collapsed)
            self.optimise()
    
    def optimise(self):  # remove duplicate points
        seen_vects = []
        changes = {}
        offset = 0
        for i, v in enumerate(self.points):
            for j, w in enumerate(seen_vects):  #O(n^2)?
                if v.value == w.value:
                    changes[i] = j
                    offset += 1
                    break
            else:
                seen_vects.append(v)
                changes[i] = i-offset

        self.points = seen_vects  # replace list with duplicates            
        self.lines = [{changes[i], changes[j]} for i,j in self.lines]  # replace duplicate points in lines
        new_lines = []
        for l in self.lines:
            if l not in new_lines:
                new_lines.append(l)
        self.lines = new_lines  # remove duplicate lines


class ShapeCombination(Shape):
    def __init__(self, *shapes, shift=v0, trans=m1):
        self.reset()
        for shape in shapes:
            offset = len(self.points)
            self.points += shape.points
            self.lines += [(i1+offset, i2+offset) for i1,i2 in shape.lines]
        self.move_to(shift)
        self.transform(trans)
        self.optimise()


class Cube(Shape):
    DEFAULT_POINTS = list(map(conv, (
        (0,0,0), (0,0,1), (1,0,1), (1,0,0),
        (0,1,0), (0,1,1), (1,1,1), (1,1,0),
    )))
    LINES = [
        {0,1}, {1,2}, {2,3}, {3,0},
        {4,5}, {5,6}, {6,7}, {7,4},
        {0,4}, {1,5}, {2,6}, {3,7}]


class SquarePyramid(Shape):
    DEFAULT_POINTS = list(map(conv, (
        (0,0,0), (0,0,1), (1,0,1), (1,0,0),
        (0.5, 1, 0.5),
    )))
    LINES = [
        {0,1}, {1,2}, {2,3}, {3,0},
        {0,4}, {1,4}, {2,4}, {3,4}]
        