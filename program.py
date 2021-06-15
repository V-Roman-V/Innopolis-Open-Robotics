from collections import deque

# Сокращения для более удобного вызова функций
mr = brick.motor(M3).setPower
ml = brick.motor(M4).setPower
el = brick.encoder(E3).read
er = brick.encoder(E4).read
sr = brick.sensor(A2).read
sl = brick.sensor(A1).read
sf = brick.sensor(A3).read
sinv = brick.sensor(A4).read
sT = brick.sensor(A5).read
wait = script.wait


def guess_type(*sensors):  # left, forward, right
    types = {
        str([1, 0, 1]): "forward",
        str([0, 0, 0]): "cross",
        str([1, 1, 1]): "typik",
        str([1, 1, 0]): "right",
        str([0, 1, 1]): "left",
        str([0, 1, 0]): "T",
        str([0, 0, 1]): "leftforward",
        str([1, 0, 0]): "rightforward",
    }
    list = [int(x < 35) for x in args] if sinv() <= 50 else [int(x > 65) for x in args]
    print(types[str(list)])
    return list


def get_way_mass(ind):
    """Возвращает массив значение с датчиков в базие поля"""
    if ind == 6:
        return [0, 1, 0, 1]
    arr = [0] + guess_type(sl(), sf(), sr())
    return arr[get_dir() :] + arr[: get_dir()]


def get_dir():
    """Возвращает направление робота"""
    return int(yaw() + 45) % 360 // 90


def gyro_calibrate():
    """Колибровка гироскопа"""
    brick.gyroscope().calibrate(2000)
    wait(2100)


def yaw() -> float:
    """Возвращает угол вращения робота от 0 до 360, 0 это вверх, поворот по часовой стрелки"""
    # 0 по гироскопу это вправо поэтому +90 для выравнивания
    return (brick.gyroscope().read()[6] / 1000.0 + 90) % 360


def get_angle(angle) -> float:
    """Возвращает разницу угла робота до цели от -180 до 180"""
    # Пример угол робота 45, нужно повернуться в 300, функция вернет -105, то есть влево на 105 градусов
    dif = angle - yaw()
    if dif > 180:
        dif = dif - 360 if dif > 180 else +360 if dif < 180 else 0
    if dif < -180:
        dif = dif + 360
    return dif


class Robot:
    """Класс для взаимодествия с роботом"""

    # Стартовые координаты робота
    x = 2
    y = 3
    start_pos = [x, y]

    def stop_motor(self):
        """Остановка моторов"""
        ml(0)
        mr(0)

    def start_motor(self, pleft, pright):
        """Запуск моторов"""
        ml(pleft)
        mr(pright)

    def straight_move(self, leng, power=60):
        """Езда прямо без линии на определенное расстояние регулируясь по гироскопу"""
        p = 2  # Коэффициент P
        angle = yaw()
        start = (el() + er()) / 2
        cur = start
        while abs(start - cur) < leng:
            cur = (el() + er()) / 2
            regul = p * get_angle(angle)
            self.start_motor(power + regul, power - regul)
            wait(1)
        self.stop_motor()

    def straight_move_line(self):
        """Езда прямо по линии на определенное расстояние регулируясь по гироскопу"""
        power = 30  # Средняя мощность
        p = 2  # Коэффициент P
        angle = yaw()
        start = (el() + er()) / 2
        cur = start
        while sinv() < 50:
            cur = (el() + er()) / 2
            regul = p * get_angle(angle)
            self.start_motor(power + regul, power - regul)
            wait(1)
        self.stop_motor()

    def back_move(self, leng):
        """Езда прямо без линии на определенное расстояние регулируясь по гироскопу"""
        power = 40  # Средняя мощность
        p = 2  # Коэффициент P
        angle = yaw()
        start = (el() + er()) / 2
        cur = start
        while abs(start - cur) < leng:
            cur = (el() + er()) / 2
            regul = p * get_angle(angle)
            self.start_motor(-power + regul, -power - regul)
            wait(1)
        self.stop_motor()

    def turn(self, right: bool):
        dirr = 1 if right else -1
        self.rotate_to((yaw() + (45 * dirr)) % 360)
        self.straight_move(265)  # 265 
        wait(100)
        self.rotate_to((yaw() + (45 * dirr)) % 360)
        self.straight_move(340)  # 340

    def followLine(self, leng, white: bool):
        """Функция езды по линии на расстояние leng по PD регулятору с учетом цвета"""

        def getErr(white) -> int:
            return sl() - sr() if white else sr() - sl()

        power = 60  # Средняя мощность
        p = 1  # Коэффициент P
        d = 1  # Коэффициент D

        start = (el() + er()) / 2
        cur = start

        old_err = getErr(white)
        while abs(start - cur) < leng:
            cur = (el() + er()) / 2
            error = getErr(white)

            regul = p * error + d * (error - old_err)

            self.start_motor(power + regul, power - regul)
        self.stop_motor()

    def rotate_to(self, _dir: int):
        """Функция для поворота робота в нужное направление"""
        while abs(get_angle(_dir)) > 0.2:
            dif = get_angle(_dir)
            pow = 7 + 43 * abs(dif) / 180  # Плвная регулировка скорости
            if dif > 0:
                self.start_motor(pow, -pow)
            else:
                self.start_motor(-pow, pow)
            wait(1)
        self.stop_motor()

    def where_to_go(self, map, path):  # Очень плохая и неправильная функция TODO
        """Возвращает направление следующей клетки. При этом удаляя первый элемент в пути и меняя координаты робота"""
        # 0 - вверх 1 - вправо 2 - вниз 3 - влево
        next = path.pop(0)
        robot_pos = map.get_ind(self.x, self.y)
        if next + 6 == robot_pos:
            self.y -= 1
            return 0
        if next - 6 == robot_pos:
            self.y += 1
            return 2
        if next - 1 == robot_pos:
            self.x += 1
            return 1
        if next + 1 == robot_pos:
            self.x -= 1
            return 3
        print(12312312312, next, robot_pos)

    def readBarCode(self):
        """Функция для чтения штрихкода"""
        data = []
        for i in range(6):
            self.straight_move(leng=60, power=20)
            wait(200)
            data.append(int(sinv() > 50))
            print(data)
        cords = [0, 0]  # [x, y]
        for i in range(3):
            cords[0] += data[i] << i
            cords[1] += data[3 + i] << i
        print(cords)
        return cords


class Map:
    """Класс объекта карты"""

    def __init__(self, width, height):
        """Создание карты"""
        self.width = 6
        self.height = 6
        self.map = [
            [0] * 4 for i in range(width * height)
        ]  # Для карты 0 - есть путь, 1 - нет пути
        # set borders
        for i in range(width):
            self.map[i][0] = 1  # up
            self.map[-i - 1][2] = 1  # down
        for i in range(height):
            self.map[i * width][3] = 1  # left
            self.map[i * width - 1][1] = 1  # right
        self.map[6][1] = 1
        self.map[7][3] = 1

    def connected(self, ind) -> list:
        """Возвращает лист вершин доступных из данной"""
        shift = [-self.width, 1, self.width, -1]
        connect = []
        for i in range(4):
            if self.map[ind][i] == 0 and self.map[ind + shift[i]][(i + 2) % 4] == 0:
                connect.append(ind + shift[i])
        return connect

    def get_ind(self, x, y) -> int:
        return x + y * self.width

    def get_path(self, start, finish) -> list:
        """Функция для поиска порядка вершин для перемещения от клетки старта к клетки финиша"""
        previous = [None for i in range(self.width * self.height)]
        previous[start] = -1

        # Тело алгоритма
        Q = deque()  # BFS - так как очередь
        Q.append(start)
        while Q:
            from_ = Q.popleft()
            for to in self.connected(from_):
                if previous[to] is None:
                    Q.append(to)
                    previous[to] = from_
        # Разматывание пути
        path = []
        cur = finish
        if previous[cur] is None:
            print("There is no path")
            return path
        while previous[cur] != -1:
            path.append(cur)
            cur = previous[cur]
        path.reverse()
        return path


class Program:
    """Основной класс для управления поведением робота"""

    # 695 => 407.12, 700 => 410,05
    robot = Robot()
    map = Map(width=6, height=6)

    def update_cell(self, cell: int, mas):
        """Функция оновления путей для текущей клетки"""
        # Для карты 0 - есть путь, 1 - нет пути
        self.map.map[cell] = mas

    def move_path(self, path):
        """Функция для движения по вершинам графа"""
        raise NotImplementedError("Move path is not implemented")

    def execMain(self):
        """Главная для исполнения функция"""
        gyro_calibrate()

        def robot_ind():
            """Функция возвращает индекс робота на поле"""
            return self.map.get_ind(self.robot.x, self.robot.y)

        # Отъезд назад на пол клетки
        self.robot.back_move(160)
        self.robot.rotate_to(90)

        self.update_cell(robot_ind(), get_way_mass(robot_ind()))
        print(self.map.map[robot_ind()])
        script.wait(150)
        self.robot.straight_move(160)
        # self.robot.rotate_to((yaw()+(90))%360)
        #    self.robot.turn(False)

        #    self.map.map[0][1]=1
        #    self.map.map[6][1]=1

        start = robot_ind()
        finish = self.map.get_ind(0, 1)
        path = self.map.get_path(start, finish)
        print(path)

        def ababaa():
            isInverse = True if sinv() > 50 else False
            print(f"st {sT()}, sr {sr()}, sl {sl()}")
            if not isInverse:
                return (sT() < 50) and (sr() > 35 or sl() > 35)
            else:
                return False

        next_move_turn = False

        while len(path) > 0:
            print(len(path))
            next_dir = self.robot.where_to_go(self.map, path)
            print(self.robot.x, self.robot.y, "nextCORDS")
            if next_move_turn:
                if ((next_dir - get_dir()) % 4) == 1:  # вправо
                    self.robot.turn(True)
                elif ((get_dir() - next_dir) % 4) == 1:  # влево
                    self.robot.turn(False)
                else:
                    self.robot.rotate_to(90 * next_dir)
                    self.robot.straight_move(700 / 4 * 3)
                    self.update_cell(robot_ind(), get_way_mass(robot_ind()))
                next_move_turn = False
            else:
                self.robot.rotate_to(90 * next_dir)
                self.robot.straight_move(700 / 4 * 3)
                self.update_cell(robot_ind(), get_way_mass(robot_ind()))
            if ababaa():
                next_move_turn = True
            else:
                self.robot.straight_move(700 / 4 * 1)
                self.robot.rotate_to(90 * get_dir())
            if ababaa() and sf() > 50:
                self.robot.straight_move(700 / 4 * 1)
            start = robot_ind()
            finish = self.map.get_ind(0, 1)
            path = self.map.get_path(start, finish)
            script.wait(1)
        script.wait(3999)
        self.robot.rotate_to(90 * get_dir())
        self.robot.straight_move_line()
        self.robot.straight_move(15, 20)
        script.wait(2000)
        station_pos = self.robot.readBarCode()
        self.robot.straight_move(235)
        script.wait(100)

        start = robot_ind()
        finish = self.map.get_ind(station_pos[0], station_pos[1])
        path = self.map.get_path(start, finish)
        print(path)

        while len(path) > 0:
            print(len(path))
            next_dir = self.robot.where_to_go(self.map, path)
            print(self.robot.x, self.robot.y, "nextCORDS")
            if next_move_turn:
                if ((next_dir - get_dir()) % 4) == 1:  # вправо
                    self.robot.turn(True)
                elif ((get_dir() - next_dir) % 4) == 1:  # влево
                    self.robot.turn(False)
                else:
                    self.robot.rotate_to(90 * next_dir)
                    self.robot.straight_move(705 / 4 * 3)
                    wait(500)
                    self.update_cell(robot_ind(), get_way_mass(robot_ind()))
                next_move_turn = False
            else:
                self.robot.rotate_to(90 * next_dir)
                self.robot.straight_move(705 / 4 * 3)
                wait(500)
                self.update_cell(robot_ind(), get_way_mass(robot_ind()))
            if ababaa():
                next_move_turn = True
            else:
                self.robot.straight_move(705 / 4 * 1)
                self.robot.rotate_to(90 * get_dir())
            if ababaa() and sf() > 50:
                self.robot.straight_move(705 / 4 * 1)
        brick.display().addLabel("STATION", 10, 20)
        brick.display().redraw()
        wait(3000)

        start = robot_ind()
        finish = self.map.get_ind(self.robot.start_pos[0], self.robot.start_pos[1])
        path = self.map.get_path(start, finish)
        print(path)

        while len(path) > 0:
            print(len(path))
            next_dir = self.robot.where_to_go(self.map, path)
            print("a")
            self.robot.rotate_to(90 * next_dir)
            print("b")
            self.robot.straight_move(700 / 4 * 3)
            print("o")
            self.update_cell(robot_ind(), get_way_mass(robot_ind()))
            print("ba")
            self.robot.straight_move(700 / 4 * 1)
            start = robot_ind()
            finish = self.map.get_ind(self.robot.start_pos[0], self.robot.start_pos[1])
            path = self.map.get_path(start, finish)
            script.wait(1)


def main():
    program = Program()
    program.execMain()


if __name__ == "__main__":
    main()
