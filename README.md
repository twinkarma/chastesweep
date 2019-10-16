# Chaste Parameter Sweeper

A tool to assist with parameter sweeping for Chaste on the HPC. It can also be applied to any other application that correctly accepts the parameter in the correct format.

## Installation

### By pip

Install by using:

```
pip install chastesweep
```

### From repository

```
# Clone the respository then install it
git clone https://github.com/twinkarma/chastesweep.git
cd chastesweep
python setup.py install
```


## Parameter Sweeping Tutorial

In this tutorial we will go through how to setup chaste for parameter sweeping on the HPC cluster. Run this tutorial directly on the cluster to be able to follow all examples including job submission.

### 1. Getting a compute node

When logging in to ShARC or Bessemer, you'll start off on a login node. You'll want to get an interactive session on a worker node to start development:


```
# On ShARC
qrshx
```

```
# Bessemer
srun --pty bash -i
```

You'll see the console change from `login` to `node` e.g. `[username@sharc-login#] $` to `[username@sharc-node###] $` in the case of ShARC. 


### 2. Install chastesweep python package

 
#### On ShARC
 
It is recommended to create a virtual environment on ShARC:
 
```
# Load the python module
module load apps/python/anaconda3-4.2.0

# Create a new virtual python environment called my_chaste_env with python 2.7
conda create -n my_chaste_env python=2.7

# Activate the environment
source activate my_chaste_env

# Install the chastesweep package
pip install chastesweep

```

#### On Bessemer

Equivalent code on Bessemer

```
# Load the python module
module load Anaconda3/5.3.0

# Create a new virtual python environment called my_chaste_env with python 2.7
conda create -n my_chaste_env2 python=2.7 chastesweep

# Activate the environment
source activate my_chaste_env2

# Install the chastesweep package
pip install chastesweep
```
 


### 3. Development Environment, pulling a a Singularity image

ShARC and Bessemer supports the [Singularity](https://sylabs.io/docs/) containerisation technology. The use of containers allow us to standardise the development environment and build dependencies on your local machine and your cluster. 

Note: On your local machine, if you're not developing on Linux, it is also possible to use docker instead. You will want to install either [Singularity](https://sylabs.io/docs/) or [docker](https://docker.com) on your local machine.

To get the latest Singularity image of Chaste, run the following:

```
singularity pull docker://chaste/chaste-docker:latest
```

You should see a file `chaste-docker_latest.sif`. 

Run the following to get into the image's bash shell:

```
singularity exec chaste-docker_latest.sif /bin/bash
```

You're now actually inside the image, try running the command `cat /etc/lsb-release` to see the current Ubuntu version e.g.:

```
cat /etc/lsb-release
DISTRIB_ID=Ubuntu
DISTRIB_RELEASE=19.04
DISTRIB_CODENAME=disco
DISTRIB_DESCRIPTION="Ubuntu 19.04"
```

You can run `exit` to exit from the image.

Singularity's `exec` command can be used to run any program from inside the image without needing to go into the interactive session. This is useful when we're running our tasks in a batch script. For example, to get the Ubuntu version as above:

```
singularity exec chaste-docker_latest.sif cat /etc/lsb-release
```

You will be using the image you've just pulled to do the building and running of the code using the `exec` command as shown above.

Note: As you will only be using the container for its build dependency, you will not need to modify the image during development and so should not need admin permission.  


### 4. Preparing your code

You now need your own version of Chaste code. The Chaste repository can be found at [https://github.com/Chaste/Chaste](https://github.com/Chaste/Chaste) and this can be forked or cloned directly depending on your requirements. We will just clone directly in this example:

```
# Clone the Chaste source code into our home folder
git clone https://github.com/Chaste/Chaste.git ~/Chaste

# Go inside the folder
cd ~/Chaste
```

The above command clones Chaste code into the `Chaste` folder to your home directory. You will now need create a custom Chaste app or project with a main() function to be able to accept parameters.

The the instructions on how to create  Chaste executable apps and user project can be followed below:
  * Make executable apps: https://chaste.cs.ox.ac.uk/trac/wiki/ChasteGuides/BuildingExecutableApps
  * User projects: https://chaste.cs.ox.ac.uk/trac/wiki/ChasteGuides/UserProjects
  
For this example we'll go with the executable app route due to the simpler setup. We'll ask the tool to generate the `.cpp` file for us.

We'll call our app `ParamSweep` and will use three parameters for this example, named `param0`, `param1` and `param2`. To automatically generate a template using the parameter sweeper tool, call:

```
chastesweep_genmain param0,param1,param2 apps/src/ParamSweep.cpp
```

The generated source code is printed on screen as well as created for you.

We can then try to build the project using `cmake`:

```
# Go into the build directory
cd build

# Generate makefiles using cmake from inside the Chaste image
singularity exec chaste-docker_latest.sif cmake ..

# Build our ParamSweep app from inside the Chaste image
singularity exec chaste-docker_latest.sif make ParamSweep
```

After the build has finished, we can now run our app:

```
singularity exec chaste-docker_latest.sif apps/ParamSweep
```

Your code should execute as is but you'll get errors stating that parameters are missing.
	

### 5. Passing parameters to the main function

The parameter sweeper follows the boost::program_options format, where each parameter is passed in the format of `--param_name param_value` e.g. for our `ParamSweep` app: 

```
singularity exec chaste-docker_latest.sif apps/ParamSweep --output_dir "/outtput/path/1" --param0 0.2 --param1 3 --param2 -0.53 
```

Note: The `output_dir` parameter is always passed to your app and all outputs of the app should be enforced to only write to this directory.


### 6. Declaring parameters and generating the batch script

Now that we have an executable ready for accepting parameters, we'll move on to declaring the values of parameters to be explored and generating batch script for submitting a batch task. For this purpose, python API has been created, the class `ParamSweeper` has been created to facilitate this parameter sweeping process. 

We create a python script named `sweep.py` for defining our parameter and creating a batch job:

```
import numpy as np
from chastesweep import ParamSweeper
p = {}
p['param0'] = np.linspace(0, 10, 5)
p['param1'] = np.linspace(0.1, -0.5, 5)
p['param2'] = [10, 20, 30]

exec_cmd = "~/Chaste/build/apps/ParamSweep"
output_dir = "~/Chaste/build/sweep_results"

# Generate batch for SGE
sweeper = ParamSweeper()
sweeper.generate_batch_output(output_dir=output_dir,
                              exec_cmd=exec_cmd,
                              parameters=p,
                              scheduler=ParamSweeper.SGE,
                              batch_params=["-M myemail@mydomain.com", "-m bes"])
```

Notice that we can additional parameters to the batch script by adding to `batch_params`. In our example we've set the scheduler to alert us of the job status `-m bes` and provided our e-mail `-M myemail@mydomain.com`.

We then run the `sweep.py` script:

```
python sweep.py
```

In the output directory `~/Chaste/build/sweep_results`, you will see the `params.json`, `runsimulation.py` and `batch.sge.sh` file. 

  * `params.json` Contains an expanded list of parameters that will be explored.
  * `batch.sge.sh` Batch script containing a task array for running through all of the parameters to be explored.
  * `runsimulation.py` Simulation runner script for running individual instances of the simulation.   


You can submit this file to the SGE scheduler to start your parameter sweeping task:

```
qsub ~/Chaste/build/sweep_results/batch.sge.sh
```

If we're running on Bessemer or other cluster that uses SLURM scheduler, simply change the `scheduler=ParamSweeper.SGE` to `scheduler=ParamSweeper.SLURM`. You'll also want to change your `batch_params` parameters as they'll likely be different from SGE. Your batch submit command will also change to:
 
```
sbatch ~/Chaste/build/sweep_results/batch.slurm.sh
```



### 7. Running the sweep locally 

Sweep can also be run locally on your machine with the `perform_serial_sweep` function:

```
import numpy as np
from chastesweep import ParamSweeper
p = {}
p['a'] = np.linspace(0, 10, 5)
p['b'] = np.linspace(0.1, -0.5, 5)
p['c'] = [10, 20, 30]

# Feed to param sweeper
sweeper = ParamSweeper()

exec_cmd = "~/Chaste/build/apps/ParamSweep"
output_dir = "~/Chaste/build/sweep_results"

sweeper.perform_serial_sweep(output_dir=output_dir, exec_cmd=exec_cmd, parameters=p)
```



