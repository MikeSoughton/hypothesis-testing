## Running jet-cnn code

The main files within this directory accomplish three main points: training the CNN on jet images, making predictions on type of jets within new data, and performing a simple hypothesis test to ascertain the significance level at which data can be said to be containing top jets. 

### Training the CNN and making predictions without bootstrapping

To train the CNN run 
```
python KerasCNN.py
```
This takes in data of QCD and top jet images, stored within `Data`, and outputs a trained CNN h5 model file within a new directory called `model_cnn`.

To make predictions over new data run
```
python predictions.py
```
which uses the trained CNN model to find the probability of jet images from the testing data of being a top jet. These probabilities are saved within `cnn_outputs`.

### Training the CNN and making predictions with bootstrapping

One can also train the CNN with bootstrapping to account for uncertainties in the training process. To do this run
```
python KerasCNN_bootstrap.py
```
This trains the CNN over $N$ bootstraps and now, instead of saving a trained CNN model file, the predictions (as well as truth data and training scores) from each iteration of the bootstrapping are saved directly to `bootstrap_arrays`. There is therefore no need to run a seperate script for predictions (note that `predictions_from_bootstrap.py` is legacy experimental code and is no longer needed).

One should then run
```
python bootstrap_analysis.py
```
to find the average PDFs of the predictions from bootstrapping which are then saved to `cnn_outputs`. This script also returns plots which analyse the results from bootstrapping.

### Running the Log-Likelihood Ratio simple hypothesis test

To perform the hypothesis test run
```
python jet_llr.py
```
This 


