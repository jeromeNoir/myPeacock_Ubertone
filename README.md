# myPeacock_Ubertone

## create a environment
  * Best: Use the Anaconda Navigator
  * Alternative:
    conda create --name Ubertone python=3.11.11

## activate the environment:
  conda activate dpivsoft

## install requirement:
 * pySerial: pip install pySerial==3.5

## To use the API locally:
 * clone/copy the directory 'USING local API' on your local computer where you want to use it and run the jupyther Notebook : 'peacock_notebook_global.ipynb'

## to use the API globally:
 * clone/copy the directory 'USING global API/API' in a temporary diectory on your local computer.
 * you need to locate the site-package directory of your python of the active 'Ubertone' env: _which python_
 * go the python site-package diectory of your env: e.g. _cd /Users/jeromenoir/anaconda3/envs/Ubertone/lib/python3.11/site-packages/_
 * create the ubertone diectory (don't use capital letters): _mkdir ubertone_ and go to this directory: _cd ubertone_
 * from the ubertone directory, copy all the files from the directory '<PATH to Temporary directory>/USING global API/API' in the 'ubertone' directory:
     cp -r <PATH to Temporary directory>/USING global API/API/* .
 * copy the jupyter Notebook 'peacock_notebook_global.ipynb' and the config file 'myConfig.json' in the directory where you want to use the code. You don't need the directory 'API' anyore.


    
