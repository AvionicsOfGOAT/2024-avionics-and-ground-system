import time
from multiprocessing import Process, Queue

from data_processor import DataProcessor
from database import Database
from decision_maker import DecisionMaker
from parachute import Parachute
from sensor import Bmp, Ebimu, Gps


def main():
    bmp = Bmp()
    ebimu = Ebimu()
    gps = Gps()
    db = Database()

    bmp_queue = Queue()
    ebimu_queue = Queue()
    gps_queue = Queue()
    database_queue = Queue()

    bmp_process = Process(target=bmp.reader, args=(bmp_queue,))
    ebimu_process = Process(target=ebimu.reader, args=(ebimu_queue,))
    gps_process = Process(target=gps.reader, args=(gps_queue,))
    database_process = Process(target=db.saver, args=(database_queue,))

    bmp_process.daemon = True
    ebimu_process.daemon = True
    gps_process.daemon = True
    database_process.daemon = True

    bmp_process.start()
    ebimu_process.start()
    gps_process.start()
    database_process.start()

    parachute = Parachute()
    decision_maker = DecisionMaker()
    data_processor = DataProcessor()

    is_altitude_descent = False
    is_descent_angle = False
    is_force_ejection_active = False
    for i in range(10):
        database_queue.put(["PARASHUTE", 0])
        database_queue.put(["ATBD", 0])
        database_queue.put(["AGBD", 0])
        database_queue.put(["FE", 0])
    for i in range(10, -1, -1):
        time.sleep(1)
        print(i)
    atbd = 0
    agbd = 0
    fe = 0
    last_time = time.time()
    print("started.")
    while True:
        current_time = time.time()
        bmp_value = -1
        ebimu_value = -1
        gps_value = -1
        if not bmp_queue.empty():
            bmp_value = bmp_queue.get()
            database_queue.put([bmp.name, bmp_value])
            # print(bmp_value)
        if not ebimu_queue.empty():
            ebimu_value = ebimu_queue.get()
            database_queue.put([ebimu.name, ebimu_value])
            # print(ebimu_value)
        if not gps_queue.empty():
            gps_value = gps_queue.get()
            database_queue.put([gps.name, gps_value])
            print(gps_value)
        exact_position = [0, 0, 0]

        decision_maker.is_in_critical_area(exact_position)
        if bmp_value != -1:
            if current_time - last_time >= 0.1:
                last_time = current_time
                is_altitude_descent = decision_maker.is_altitude_descent(bmp_value)
        if ebimu_value != -1:
            is_descent_angle = decision_maker.is_descent_angle(ebimu_value)
        is_force_ejection_active = decision_maker.is_force_ejection_active()

        parachute_status = parachute.is_parachute_deployed
        if is_altitude_descent:
            if parachute_status == False:
                parachute.deploy()
            if atbd == 0:
                atbd = 1
                database_queue.put(["ATBD", 1])
                database_queue.put(["PARASHUTE", 1])
        if is_descent_angle and False:
            if parachute_status == False:
                parachute.deploy()
            if agbd == 0:
                agbd = 1
                database_queue.put(["AGBD", 1])
                database_queue.put(["PARASHUTE", 1])
        if is_force_ejection_active:
            print("FE")
            if parachute_status == False:
                parachute.deploy()
            if fe == 0:
                fe = 1
                database_queue.put(["PARASHUTE", 2])


if __name__ == "__main__":
    main()
