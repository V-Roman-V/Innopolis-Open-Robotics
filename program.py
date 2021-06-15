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

types = {
  str([0, 0, 1]): 'forward',
  str([1, 1, 1]): 'cross',
  str([0, 0, 0]): 'typik',
  str([0, 1, 0]): 'right',
  str([1, 0, 0]): 'left',
  str([1, 1, 0]): 'T',
  str([1, 0, 1]): 'leftforward',
  str([0, 1, 1]): 'rightforward'
}

def guess_type(*args):
  try:
    isInverse = True if sinv() > 50 else False
    if not isInverse:
      print(types[str(list(map(lambda x: 0 if x < 50 else 1, args)))])
      return list(map(lambda x: 1 if x < 50 else 0, args))
    else:
      print(types[str(list(map(lambda x: 1 if x < 50 else 0, args)))])
      return list(map(lambda x: 0 if x < 50 else 1, args))
  except:
    return 'NO'

def get_way_mass(ind):
  mas = guess_type(sl(), sr(), sf())
  converter = {
    0: [mas[2], mas[1], 0, mas[0]],
    1: [mas[0], mas[2], mas[1], 0],
    2: [0, mas[0], mas[2], mas[1]],
    3: [mas[1], 0, mas[0], mas[2]],
  }
  if ind != 6:
    return converter[get_dir()] # 0 - есть путь 1 - нет
  else:
    return [0, 1, 0, 1]
  
def get_dir():
  rot = yaw()
  if 315 < rot or rot < 45:
   return 0
  if 135 > rot > 45:
   return 1
  if 225 > rot > 135:
   return 2
  if 315 > rot > 225:
   return 3 

def gyro_calibrate():
  """Колибровка гироскопа""" 
  brick.gyroscope().calibrate(2000)
  wait(2100)
  
  
def yaw() -> float:
  """Возвращает угол вращения робота от 0 до 360, 0 это вверх, поворот по часовой стрелки"""
  # 0 по гироскопу это вправо поэтому +90 для выравнивания
  return (brick.gyroscope().read()[6]/1000. + 90)%360




def get_angle(angle) -> float:

  """Возвращает разницу угла робота до цели от -180 до 180"""

  # Пример угол робота 45, нужно повернуться в 300, функция вернет -105, то есть влево на 105 градусов

  dif = angle - yaw()

  if dif > 180:

    dif = dif -360 if dif>180 else +360 if dif<180 else 0

  if dif < -180:

    dif = dif + 360

  return dif



class Robot():
  """Класс для взаимодествия с роботом"""
  # Стартовые координаты робота
  x = 2
  y = 3
  start_pos = [x, y]
  dir = 1 # 0-вверх, 1-вправо, 2-вниз, 3-влево
  
  def smooth_turn_right(self):
    self.straight_move()
  
  def stop_motor(self):
    """Остановка моторов"""
    ml(0)
    mr(0)

  def start_motor(self, pleft, pright):
    """Запуск моторов"""
    ml(pleft)
    mr(pright)

    

  def straight_move(self, leng):
    """Езда прямо без линии на определенное расстояние регулируясь по гироскопу"""
    power = 60 # Средняя мощность
    p = 2 # Коэффициент P
    angle = yaw()
    start = (el() + er())/2
    cur = start
    while abs(start - cur) < leng:
      cur = (el() + er())/2
      regul = p * get_angle(angle)
      self.start_motor( power+regul, power-regul )
      wait(1)
    self.stop_motor()
    
  def straight_move_line(self):
    """Езда прямо по линии на определенное расстояние регулируясь по гироскопу"""
    power = 30 # Средняя мощность
    p = 2 # Коэффициент P
    angle = yaw()
    start = (el() + er())/2
    cur = start
    while sinv() < 50:
      cur = (el() + er())/2
      regul = p * get_angle(angle)
      self.start_motor( power+regul, power-regul )
      wait(1)
    self.stop_motor()


  def back_move(self, leng):
    """Езда прямо без линии на определенное расстояние регулируясь по гироскопу"""
    power = 40 # Средняя мощность
    p = 1 # Коэффициент P
    angle = yaw()
    start = (el() + er())/2
    cur = start
    while abs(start - cur) < leng:
      cur = (el() + er())/2
      regul = p * get_angle(angle)
      self.start_motor( -(power+regul), -(power-regul) )
      wait(1)
    self.stop_motor()

  def turn(self, right: bool):
    if right:
      dirr = 1
    else:
      dirr = -1
    self.rotate_to((yaw()+(45*dirr))%360)
    self.straight_move(265) # 265 !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    wait(100)
    self.rotate_to((yaw()+(45*dirr))%360)
    self.straight_move(340) # 340
    
  def turn1(self, right: bool):
    if right:
      dirr = 1
    else:
      dirr = -1
    self.back_move(115) # 0
    self.rotate_to((yaw()+(45*dirr))%360)
    self.straight_move(430) # 265 !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    wait(100)
    self.rotate_to((yaw()+(45*dirr))%360)
    self.straight_move(210) # 340
    


  def followLine(self, leng, white: bool):
    """Функция езды по линии на расстояние leng по PD регулятору с учетом цвета"""
    def getErr(white)->int:
      return sl()-sr() if white else sr()-sl()
      #Инвертируется показания каждого датчика. (100-sl()) - (100-sr())
    
    power = 60 # Средняя мощность
    p = 1 # Коэффициент P
    d = 1 # Коэффициент D
    
    start = (el() + er())/2
    cur = start
    
    old_err = getErr(white)
    while abs(start - cur) < leng:
      cur = (el() + er())/2
      error = getErr(white)
      
      regul = p * error + d * (error - old_err)
      
      self.start_motor( power+regul, power-regul )
    self.stop_motor()
  
  def move_forward(self):
    """Функция для проезда вперед на одну клетку"""
    self.x += (self.dir==1) - (self.dir==3)
    self.y += (self.dir==2) - (self.dir==0)
    raise NotImplementedError('Move forward is not implemented')
  
  def rotate_to(self, _dir: int):
    """Функция для поворота робота в нужное направление"""   
    self.dir = _dir
    while abs(get_angle(_dir)) > 0.2:

      dif = get_angle(_dir)

      pow = 7 + 43*abs(dif)/180  # Плвная регулировка скорости

      if(dif > 0):

        self.start_motor(pow,-pow)

      else:

        self.start_motor(-pow,pow)
      wait(1)
    self.stop_motor()
 
  
  def is_cross(self)->bool:
    """Функция возвращает есть ли перекресток"""
    if (self.is_inverse()):
      return sl()<50 and sr()<50   
    else:
      return sl()>50 and sr()>50   
    
  def is_inverse(self)->bool:
    """Функция возвращает инвертирована ли клетка"""
    raise NotImplementedError('isInverse is not implemented')
 

  def where_to_go(self, map, path):
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
    data = []
    power = 50
    p = 1
    d = 1
    leng = 72
    start = (el() + er())/2

    cur = start

    while len(data) < 6:
      mr(power)
      ml(power)
      start = cur
      while abs(start - cur) < (leng):
        cur = (el() + er()) / 2
      ml(0)
      mr(0)
      script.wait(150)
      self.rotate_to(90 * 0) # Поворот к нулевому градусу после неравномерного старта
      data.append(1 if sf() > 50 else 0)
      print(data)
    mr(0)
    ml(0)
    if 1:
      cords = [0, 0] # [x, y]
      for i in range(3):
        cords[0] += data[i] * (2 ** i)
      data = data[3:]
      for i in range(3):
        cords[1] += data[i] * (2 ** i)
    print(cords)
    return cords
    
class Map():
  """Класс объекта карты"""
  def __init__(self, width, height):
    """Создание карты"""
    self.width = 6   
    self.height = 6
    self.map = [[0] * 4 for i in range(width*height)]  # Для карты 0 - есть путь, 1 - нет пути
    #set borders
    for i in range(width):
      self.map[i][0]=1  #up
      self.map[-i-1][2]=1  #down
    for i in range(height):
      self.map[i * width][3]=1  #left
      self.map[i * width-1][1]=1  #right
    self.map[6][1] = 1
    self.map[7][3] = 1
    
  def connected(self, ind)->list:
    """Возвращает лист вершин доступных из данной"""
    shift = [-self.width, 1, self.width, -1]
    connect = []
    for i in range(4):
      if self.map[ind][i] == 0 and self.map[ind + shift[i]][(i+2)%4] == 0:
        connect.append( ind + shift[i])
    return connect

    

  def get_ind(self, x, y)->int:
    return x+y*self.width


  def get_path(self, start, finish)->list:
    """Функция для поиска порядка вершин для перемещения от клетки старта к клетки финиша"""
    previous = [None for i in range(self.width*self.height)]
    previous[start] = -1

    # Тело алгоритма
    Q = deque() # BFS - так как очередь
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

class Program():
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
    raise NotImplementedError('Move path is not implemented')
  
  def execMain(self):
    """Главная для исполнения функция"""    
    gyro_calibrate()

#    self.robot.rotate_to(0)

    #self.robot.straight_move(720 / 2)
    #self.robot.straight_move(185)

    self.robot.back_move(160)
    self.robot.rotate_to(90)
    self.update_cell(self.map.get_ind(self.robot.x, self.robot.y), get_way_mass(self.map.get_ind(self.robot.x, self.robot.y)))
    print(self.map.map[self.map.get_ind(self.robot.x, self.robot.y)])
    script.wait(150)
    self.robot.straight_move(160)
    #self.robot.rotate_to((yaw()+(90))%360)
#    self.robot.turn(False)

    

#    self.map.map[0][1]=1
#    self.map.map[6][1]=1

    start = self.map.get_ind(self.robot.x,self.robot.y)

    finish = self.map.get_ind(0,1)
    path = self.map.get_path(start, finish)
    print(path)
    
    
    def ababaa():
      isInverse = True if sinv() > 50 else False
      print(f'st {sT()}, sr {sr()}, sl {sl()}')
      if not isInverse:
        return (sT() < 50) and (sr() > 50 or sl() > 50)
      else:
        return False
    
    next_move_turn = False
    
    while len(path) > 1:
      print(len(path))  
      next_dir = self.robot.where_to_go(self.map, path)
      print(self.robot.x, self.robot.y, 'nextCORDS')
      if next_move_turn:
        if ((next_dir - get_dir()) % 4) == 1: # вправо
          self.robot.turn(True)
        elif ((get_dir() - next_dir) % 4) == 1: # влево
          self.robot.turn(False)
        else:
          self.robot.rotate_to(90 * next_dir)
          self.robot.straight_move(700 / 4 * 3)
          wait(500)
          self.update_cell(self.map.get_ind(self.robot.x, self.robot.y), get_way_mass(self.map.get_ind(self.robot.x, self.robot.y)))
        next_move_turn = False
      else:
        self.robot.rotate_to(90 * next_dir)
        self.robot.straight_move(700 / 4 * 3)
        wait(500)
        self.update_cell(self.map.get_ind(self.robot.x, self.robot.y), get_way_mass(self.map.get_ind(self.robot.x, self.robot.y)))
      if ababaa():
        next_move_turn = True
      else:
        self.robot.straight_move(700 / 4 * 1)
        self.robot.rotate_to(90 * get_dir())
      if ababaa() and sf() > 50:
        self.robot.straight_move(700 / 4 * 1)
      
        
      start = self.map.get_ind(self.robot.x,self.robot.y)
      finish = self.map.get_ind(0,1)
      path = self.map.get_path(start, finish)
      script.wait(1)
      
    script.wait(3999)
    next_dir = self.robot.where_to_go(self.map, path)
    self.robot.rotate_to(90 * next_dir)
    self.robot.straight_move_line()
    station_pos = self.robot.readBarCode()
    self.robot.straight_move(235)
    script.wait(100)

    start = self.map.get_ind(self.robot.x,self.robot.y)
    finish = self.map.get_ind(station_pos[0], station_pos[1])
    path = self.map.get_path(start, finish)
    print(path)
    
    while len(path) > 0:
      print(len(path))  
      next_dir = self.robot.where_to_go(self.map, path)
      print('a')
      self.robot.rotate_to(90 * next_dir)
      print('b')
      self.robot.straight_move(700 / 4 * 3)
      print('o')
      self.update_cell(self.map.get_ind(self.robot.x, self.robot.y), get_way_mass(self.map.get_ind(self.robot.x, self.robot.y)))
      print('ba')
      self.robot.straight_move(700 / 4 * 1)
      start = self.map.get_ind(self.robot.x,self.robot.y)
      finish = self.map.get_ind(station_pos[0], station_pos[1])
      path = self.map.get_path(start, finish)
      script.wait(1)

    brick.display().addLabel("STATION", 10, 20)
    brick.display().redraw()
    wait(3000)
    
    
    start = self.map.get_ind(self.robot.x,self.robot.y)
    finish = self.map.get_ind(self.robot.start_pos[0], self.robot.start_pos[1])
    path = self.map.get_path(start, finish)
    print(path)
    
    while len(path) > 0:
      print(len(path))  
      next_dir = self.robot.where_to_go(self.map, path)
      print('a')
      self.robot.rotate_to(90 * next_dir)
      print('b')
      self.robot.straight_move(700 / 4 * 3)
      print('o')
      self.update_cell(self.map.get_ind(self.robot.x, self.robot.y), get_way_mass(self.map.get_ind(self.robot.x, self.robot.y)))
      print('ba')
      self.robot.straight_move(700 / 4 * 1)
      start = self.map.get_ind(self.robot.x, self.robot.y)
      finish = self.map.get_ind(self.robot.start_pos[0], self.robot.start_pos[1])
      path = self.map.get_path(start, finish)
      script.wait(1)

def main():
  program = Program()
  program.execMain()

if __name__ == '__main__':
  main()