import os
import sys
from time import sleep

import speedtest
from colorama import Fore, init
from tqdm import tqdm


class SpeedTest:
    def __init__(self, print: bool = False, _return: bool = False):
        self.print = print
        self._return = _return
        self.speed = None

    def speed_test(self, callback: callable):
        s = speedtest.Speedtest()
        s.get_servers()
        s.get_best_server()
        s.download()
        s.upload()
        s.results.share()
        results_dict = s.results.dict()
        del s
        callback(results_dict)

    def output_callback(self):
        st = speedtest.Speedtest()

        init(autoreset=True)
        st.get_best_server()
        for _ in tqdm(range(10), colour="green", desc="Finding Optimal Server"):
            sleep(0.05)

        st.download()
        for _ in tqdm(range(10), colour="cyan", desc="Getting Download Speed"):
            sleep(0.05)

        st.upload()
        for _ in tqdm(range(10), colour="red", desc="Getting Upload Speed"):
            sleep(0.05)

        res_dict = st.results.dict()

        dwnl = str(res_dict["download"])[:2] + "." + str(res_dict["download"])[2:4]

        upl = str(res_dict["upload"])[:2] + "." + str(res_dict["upload"])[2:4]

        print("")

        print(Fore.MAGENTA + "=" * 80)
        print(Fore.GREEN + "INTERNET SPEED TEST RESULTS:".center(80))
        print(Fore.MAGENTA + "=" * 80)
        print(
            Fore.YELLOW
            + f"Download: {dwnl}mbps({float(dwnl)*0.125:.2f}MBs) | Upload:{upl}mbps ({float(upl)*0.125:.2f}MBs) | Ping: {res_dict['ping']:.2f}ms".center(
                80
            )
        )
        print(Fore.MAGENTA + "-" * 80)
        print(
            Fore.CYAN
            + f"HOST:{res_dict['server']['host']} | SPONSOR:{res_dict['server']['sponsor']} | LATENCY: {res_dict['server']['latency']:.2f}".center(
                80
            )
        )
        print(Fore.MAGENTA + "-" * 80)

        import msvcrt
        import time

        i = 0
        while True:
            i = i + 1
            if msvcrt.kbhit() and msvcrt.getwche() == "\r":
                break
            time.sleep(0.1)
        print(i)
        del st

    def main(self, print: bool = False, _return: bool = False):
        if _return:
            return_results = lambda results_dict: results_dict
            call_back = return_results
        else:
            print_results = (
                lambda results_dict: self.output_callback() if print else None
            )
            call_back = print_results
        self.speed_test(callback=call_back)


print(main(print=True))
