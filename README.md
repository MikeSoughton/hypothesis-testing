# hypothesis-testing
Repository for performing hypothesis tests using the outputs of various Machine Learning methods, associated with the paper 'A simple guide from Machine Learning outputs to statistical criteria' [arXiv:2203.03669](https://arxiv.org/abs/2203.03669) (2022). Authors: Charanjit K. Khosa, Veronica Sanz and Michael Soughton.


<!--- <div align="center"> --->
<!--- <img src=".github/Logo_main_black.png", width="300"> --->
<!--- </div> --->

-----------------

Currently there is much interest in using Machine Learning methods for detecting and identifying signals within HEP. However, little has so far been done towards the seemingly straightforward task of incorporating the results from these methods into statistical tests such as those used for discovery of new particles. Our paper demonstrates how to use the outputs of supervised classifiers or unsupervised anomaly detection methods can be used in Log-Likelihood Ratio hypothesis tests and in obtaining seperation and discovery significances. 

We train a CNN to distinguish between QCD and top jet images (in $\eta$-$p_T$ space) and then use the outputs of the CNN when applied to new data (which are the probabilities of a jet being a top jet) within a Log-Likelihood ratio hypothesis test. In doing so one can assess the degree to which the data contins signal events which we express in terms of a separation significance $\alpha$, also called the type I error. Note that $\alpha=1.35 \times 10^{-3}$ corresponds to a 3 $\sigma$ significance and $\alpha=2.87 \times 10^{-7}$ corresponds to a 5 $\sigma$ significance but by using the Log-Likelihood ratio test we obtain a stronger and dynamic significance. We run a number of toy experiments to find the optimal $\alpha$ under an aysymmetric, and a stronger symmetric, testing condition. This can be done in all situations where a good theoretical background and signal distribution can be modelled. Then when the real experiment is performed, the observed value for the test statistic can simply be compared to this. 

Events are generated through [`MadGraph`](https://arxiv.org/abs/1106.0522) along with [`Pythia`](https://arxiv.org/abs/0710.3820) and [`Delphes`](https://arxiv.org/abs/1307.6346) for showering and detector effects. 

Tensorflow etc..

The paper finds ...

The code does ...

Prerequisities ...

The code is run ...

References, funding and additional info ...

This project was made possible through funding from the Royal Society-SERB Newton International Fellowship (to C.K.K.) and the Science Technology and Facilities Council (STFC) under grant number (to V.S. and M.S.).

**Bold**

[Link](https://www.wikipedia.org)

## Section

A section can be referenced through [Section](#section)






## Citation
Please cite the paper as follows in your publications if it helps your research:

    @article{Khosa:2019kxd,
      author         = "Khosa, Charanjit K. and Sanz, Veronica and Soughton,
                        Michael",
      title          = "{WIMPs or else? Using Machine Learning to disentangle LHC
                        signatures}",
      year           = "2019",
      eprint         = "1910.06058",
      archivePrefix  = "arXiv",
      primaryClass   = "hep-ph",
      SLACcitation   = "%%CITATION = ARXIV:1910.06058;%%"
    }

## License
