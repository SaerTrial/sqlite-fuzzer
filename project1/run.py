import subprocess
import random
import csv
import argparse
import os

import matplotlib.pyplot as plt

from fuzzer import Fuzzer

def plot(x, y):
    plt.plot(x, y, linestyle='-')
    plt.xlabel('# Input')
    plt.ylabel('% Coverage')
    plt.title('Branch coverage over time')
    plt.savefig('plot.pdf')
    print("Saved plot.pdf")

class Experiment:
    def __init__(self):
        random.seed()
        self.fuzzer = Fuzzer()
        self.db_file = "empty.db"
        self.sqlite3 = self.find_sqlite3_executable()

    def find_sqlite3_executable(self):
        # Try to find sqlite3 in the current working directory or the script's directory
        script_directory = os.path.dirname(os.path.abspath(__file__))
        script_sqlite3_path = os.path.join(script_directory, "sqlite3")

        if os.path.exists(script_sqlite3_path):
            return script_sqlite3_path

        # If sqlite3 is not found in the script's directory or CWD, you can add additional paths or customize this logic.
        raise FileNotFoundError("sqlite3 executable not found. Please set the path manually.")

    def run(self, sqlcmd):
        command = f'echo "{sqlcmd}" | {self.sqlite3} {self.db_file}'
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output, error = process.communicate()

    def get_coverage(self):
        coverage_report_file = "coverage_report.csv"
        gcovr_command = f"gcovr --csv --branches --exclude-unreachable-branches -o {coverage_report_file}"
        subprocess.run(gcovr_command, shell=True, check=True)

        with open(coverage_report_file, 'r') as f:
            branch_cov_percent = None
            reader = csv.DictReader(f, delimiter=',')
            for row in reader:
                assert 'filename' in row
                assert 'branch_percent' in row
                if row['filename'] == 'sqlite3.c':
                    branch_cov_percent = float(row['branch_percent'])
                    break
            assert branch_cov_percent is not None
        return branch_cov_percent

    def clean(self):
        print("Cleaning up project directory for a new measurement...")
        # Delete old empty.db, PDFs, coverage reports
        subprocess.run("make clean", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        # Build sqlite and .gcno if not exists.
        subprocess.run("make", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print("Done.")

    def generate_and_run(self):
        self.run(self.fuzzer.fuzz_one_input())
    
    def generate_and_run_k_plot_coverage(self, k, plot_every_x):
        self.clean()

        cov = []
        old_cov = 0
        for i in range(k):
            print("Generate and run input ", i)
            self.generate_and_run()
            if plot_every_x != -1 and i%plot_every_x==0:
                old_cov = self.get_coverage()
            cov.append(old_cov)

        # Do one final coverage measurment (or the only one, if plot_every_x == -1).
        cov.append(self.get_coverage())

        plot(x=list(range(len(cov))), y=cov)

def main():
    parser = argparse.ArgumentParser(description='SQL fuzzer and coverage plotter')
    parser.add_argument('runs', type=int, help='How many inputs should be generated and run?')
    parser.add_argument('--plot-every-x', default=-1, type=int, help='Coverage will be measured after plot_every_x. (default:-1, i.e. there is only one coverage measurement at the end)')
    args = parser.parse_args()
    runs = args.runs
    plot_every_x = args.plot_every_x

    experiment = Experiment()
    experiment.generate_and_run_k_plot_coverage(runs, plot_every_x)

if __name__ == "__main__":
    main()
