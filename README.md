This is a fuzz testing project of "security testing" course taken by me in University. I did learn a lot throughout this project and may find it more useful to share this project out, giving you more insights on fuzz testing. Beware that this project focuses on memory corruption rather than logic vulnerabities, which I may work a bit on in near future. 

## Project description
In this project, one has to build a grammar-based blockbox fuzzer to test SQLite.

The Dockerfile is provided to lift up environment for fuzzing. However, running a fuzzer in the docker was a terrible experience to me and I suggest a local approach. Of course, I will detail both of ways to do fuzz testing in the preceeding section.

This project expects one to use fuzzers available in `fuzzingbook`. 

## Project structure
In the `project1` folder, only `grammar.py` and the function `fuzz_one_input` in `fuzzer.py` are allowed to be modified. Moreover, `fuzzer.py` uses the grammar defined in `grammar.py`.

Additionally, `run.py` is a wrapper, consuming a generated fuzzing input and calculting branch coverage throughout the entire testing.

### Running a fuzz testing
If one wants to generate 500 inputs for testing, refer to the preceeding command:
```
python3.10 run.py 500
```

As soon as the testing is done, `coverage_report.csv` and `plot.pdf` are automatically generated for information about coverage.

If one wants to observe progression in coverage, considers the following command:
```
python3.10 run.py --plot-every-x 100 1000
```

This command means a measurement of coverage will be done every 100 inputs out of 1000 inputs.

If one wants to access to a detailed coverage report, uses the following command:
```
make coverage-html
```

## Setting up environment

### Building a Docker image
```
docker build -t sectest .
docker run -d --name sectest_container -v sectest:/app -p 6080:80 sectest
```

After a container created from this image is spinned up, access to http://localhost:6080/, where there is an GUI-based system.

### Running locally
```
sudo apt-get update
sudo apt-get install -y python3.10 python3-pip python3.10-dev python3.10-distutils unzip nano curl libgraphviz-dev
pip install fuzzingbook jupyterlab gcovr matplotlib
cd project1
make clean && make
python3.10 run.py 500
```



## Evaluation criteria
This project is evaluated in three main metrics:
- branch coverage in sqilite3.c
- bug finding capability
- input diversity

The last two metrics were not accessible by students until my project was evaluated on the mentor's machine. This is to say, we could design our own evaluator. For example, triggering a exit or crash if some deep application logic is reached. This could be done as part of my future work in this repo.

### Limited number of inputs to be evaluated

This project only evaluates one's fuzzer with 100.000 inputs. In case that a fuzzer cannot spawn this number of fuzzing inputs within 30 mins, inputs that have been generated so far are considered. This process repeats totally three times, and the best result will be taken.





