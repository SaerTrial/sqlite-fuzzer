import os
import glob
import pickle
import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as stats
import pandas as pd

fill_color = '#ffe4c4'
dot_color = '#4f7ead'
confidence_level = 0.8
DIR = os.path.dirname(os.path.realpath(__file__))

def plot(x, y):
    plt.plot(x, y, linestyle='-')


def median_CI(data, ci, p):
	'''
	data: pandas datafame/series or numpy array
	ci: confidence level
	p: percentile' percent, for median it is 0.5
	output: a list with two elements, [lowerBound, upperBound]
	'''
	if type(data) is pd.Series or type(data) is pd.DataFrame:
		#transfer data into np.array
		data = data.values

	#flat to one dimension array
	data = data.reshape(-1)
	data = np.sort(data)
	N = data.shape[0]
	
	lowCount, upCount = stats.binom.interval(ci, N, p, loc=0)
	#given this: https://onlinecourses.science.psu.edu/stat414/node/316
	#lowCount and upCount both refers to  W's value, W follows binomial Dis.
	#lowCount need to change to lowCount-1, upCount no need to change in python indexing
	lowCount -= 1
	# print lowCount, upCount
	return data[int(lowCount)], data[int(upCount)]

def aggregate_and_plot_cov():
    covs = glob.glob(os.path.join(DIR, "cov_*.pkl"))
    equal = []
    prev_cov = None
    total_cov = []
    for cov in covs:
        assert os.path.exists(cov) 
        with open(cov, 'rb') as f:
            cur = pickle.load(f)
            if prev_cov == None:
                prev_cov = cov
            else:
                equal.append(len(prev_cov) == len(cov))
            total_cov.append(cur)
            #plot(x=list(range(len(cur))), y=cur)
    assert all(equal)
    return np.array(total_cov)


def main():
    plt.xlabel('# Input')
    plt.ylabel('% Coverage')
    plt.title('Branch coverage over time (median and interval 80%)')

    arr = aggregate_and_plot_cov()
    # get rid of column 0 since no command was executed at this moment,
    # there is no point counting coverage.
    arr = arr[:,1:]
    num_rows, num_cols = arr.shape
    print(num_rows, num_cols)
    medians = []
    lows = []
    uppers =[]
    for col in range(num_cols):
        medians.append(np.median(arr[:,col]))
        low, upper = median_CI(arr[:,col], confidence_level, 0.5)
        lows.append(low)
        uppers.append(upper)

    input_scale = list(range(len(medians)))
    plt.plot(input_scale, medians, linestyle='-')
    plt.fill_between(input_scale, lows, uppers, color='orange', alpha=0.5)
    plt.savefig('branch_coverage.pdf')

if __name__ == "__main__":
    main()
