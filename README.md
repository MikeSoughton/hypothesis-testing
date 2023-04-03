# hypothesis-testing
Repository for performing hypothesis tests using the outputs of various Machine Learning methods, associated with the paper 'A simple guide from Machine Learning outputs to statistical criteria' [arXiv:2203.03669](https://arxiv.org/abs/2203.03669) (2022). Authors: Charanjit K. Khosa, Veronica Sanz and Michael Soughton.


<!--- <div align="center"> --->
<!--- <img src=".github/Logo_main_black.png", width="300"> --->
<!--- </div> --->

-----------------

Currently there is much interest in using Machine Learning methods for detecting and identifying signals within HEP. However, little has so far been done towards the seemingly straightforward task of incorporating the results from these methods into statistical tests such as those used for discovery of new particles. Our paper demonstrates how to use the outputs of supervised classifiers or unsupervised anomaly detection methods can be used in Log-Likelihood Ratio hypothesis tests and in obtaining seperation and discovery significances. 

We train supervised Machine Learning methods (CNN and DNN classifiers) on types of signals and backgrounds that may be found within the LHC. The CNN was trained on images (in $\eta$-$p_T$ space) of QCD jets as background and top jets as signal, and the DNN on $p \, p \to Z^* \to h \,  Z  \textrm{ where } Z\to \ell^+ \ell^- \textrm{ and } h \to b \bar{b}$ with the background the interaction as occuring under the SM case and the signal as occuring under the SMEFT. We then use the outputs of the these classifiers (being the probability of a jet image being a top jet in the CNN case and the probability of an event being a SMEFT signal in the DNN case) when applied to new data within a Log-Likelihood ratio simple hypothesis test. In doing so one can assess the degree to which the data contins signal events which we express in terms of a separation significance $\alpha$, also called the type I error. Note that $\alpha=1.35 \times 10^{-3}$ corresponds to a 3 $\sigma$ significance and $\alpha=2.87 \times 10^{-7}$ corresponds to a 5 $\sigma$ significance, but by using the Log-Likelihood ratio test we obtain a stronger and dynamic significance. We run a number of toy experiments to find the optimal $\alpha$ under an aysymmetric, and a stronger symmetric, testing condition. This can be done in all situations where a good theoretical background and signal distribution can be modelled. Then when the real experiment is performed, the observed value for the test statistic can simply be compared to this. 

We also train an unsupervised VAE on a on the same Standard Model background as was the DNN classifier, but now it has no knowledge of what the SMEFT signal looks like. With the goal of using the outputs of the VAE to obtain a significance of finding SMEFT signals within the data we calculate the Reconstruction Error $R$. This is done for a number of toy experiments as in the supervised case, but now, without using truth labels, there is no signal distribution to perform a simple hypothesis test with so we instead use a generalised hypothesis test. This means that we end up with a discovery significance, akin to the Asimov significance, rather than a seperation significance or significance level. This is essentially just the $p$-value which can be compared to an arbitrary significance level such as 3 $\sigma$ or 5 $\sigma$ rather than one tailored for a specific experiment, however one gains the benefit of potentially being able to announce signal discovery without having to specify the signal beforehand.

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

    @article{Khosa:2022vxb,
    author = "Khosa, Charanjit Kaur and Sanz, Veronica and Soughton, Michael",
    title = "{A simple guide from machine learning outputs to statistical criteria in particle physics}",
    eprint = "2203.03669",
    archivePrefix = "arXiv",
    primaryClass = "hep-ph",
    doi = "10.21468/SciPostPhysCore.5.4.050",
    journal = "SciPost Phys. Core",
    volume = "5",
    pages = "050",
    year = "2022"
    }

## License
